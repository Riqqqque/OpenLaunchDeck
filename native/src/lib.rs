use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::Read;

fn parse_button_id(button_id: &str) -> Option<usize> {
    let bytes = button_id.as_bytes();
    if bytes.len() != 2 {
        return None;
    }
    let row = bytes[0];
    let column = bytes[1];
    if !(b'A'..=b'H').contains(&row) || !(b'1'..=b'8').contains(&column) {
        return None;
    }
    let row_index = (row - b'A') as usize;
    let column_index = (column - b'1') as usize;
    Some(row_index * 8 + column_index)
}

#[pyfunction]
fn validate_button_id(button_id: &str) -> bool {
    parse_button_id(button_id).is_some()
}

#[pyfunction]
fn button_id_to_index(button_id: &str) -> i32 {
    parse_button_id(button_id)
        .map(|index| index as i32)
        .unwrap_or(-1)
}

#[pyfunction]
fn index_to_button_id(index: usize) -> PyResult<String> {
    if index >= 64 {
        return Err(PyValueError::new_err("Button index out of range."));
    }
    let row = (b'A' + (index / 8) as u8) as char;
    let column = (b'1' + (index % 8) as u8) as char;
    Ok(format!("{}{}", row, column))
}

#[pyfunction]
fn calculate_profile_hash(json_text: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(json_text.as_bytes());
    format!("{:x}", hasher.finalize())
}

#[pyfunction]
fn verify_sha256(file_path: &str, expected_hash: &str) -> PyResult<bool> {
    let mut file = File::open(file_path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 1024 * 1024];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    let actual = format!("{:x}", hasher.finalize());
    Ok(actual.eq_ignore_ascii_case(expected_hash))
}

#[pymodule]
fn openlaunchdeck_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_button_id, m)?)?;
    m.add_function(wrap_pyfunction!(button_id_to_index, m)?)?;
    m.add_function(wrap_pyfunction!(index_to_button_id, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_profile_hash, m)?)?;
    m.add_function(wrap_pyfunction!(verify_sha256, m)?)?;
    Ok(())
}
