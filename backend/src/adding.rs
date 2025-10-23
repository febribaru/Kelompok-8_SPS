/// y1(t) = x1(t) + x2(t)
pub fn add_signals(x1: &[f64], x2: &[f64]) -> Vec<f64> {
    x1.iter().zip(x2.iter()).map(|(&a, &b)| a + b).collect()
}