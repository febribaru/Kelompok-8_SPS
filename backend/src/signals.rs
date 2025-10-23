use std::f64::consts::PI;

/// Menghasilkan sinyal x1(t) = A1 * sin(2πf1t + φ1)
pub fn generate_x1(t: &[f64], a: f64, f: f64, phi: f64) -> Vec<f64> {
    t.iter()
        .map(|&time| a * (2.0 * PI * f * time + phi).sin())
        .collect()
}

/// Menghasilkan sinyal x2(t) = A2 * sin(2πf2t + φ2)
pub fn generate_x2(t: &[f64], a: f64, f: f64, phi: f64) -> Vec<f64> {
    t.iter()
        .map(|&time| a * (2.0 * PI * f * time + phi).sin())
        .collect()
}