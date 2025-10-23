use actix_web::{web, App, HttpResponse, HttpServer, Responder};
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

// Import modul operasi
mod signals;
mod adding;
mod subtracting;
mod multiplying;

use signals::{generate_x1, generate_x2};
use adding::add_signals;
use subtracting::subtract_signals;
use multiplying::multiply_signals;

#[derive(Deserialize)]
struct SignalParams {
    a1: f64,
    a2: f64,
    f1: f64,
    f2: f64,
    phi1: f64,
    phi2: f64,
    t_start: f64,
    t_end: f64,
    samples: usize,
}

#[derive(Serialize)]
struct SignalResponse {
    t: Vec<f64>,
    x1: Vec<f64>,
    x2: Vec<f64>,
    y1: Vec<f64>,
    y2: Vec<f64>,
    y3: Vec<f64>,
}

async fn generate_signals(params: web::Json<SignalParams>) -> impl Responder {
    let p = params.0;

    // Validasi dasar
    if p.samples == 0 {
        return HttpResponse::BadRequest().json("samples must be > 0");
    }

    // Generate time vector
    let dt = if p.samples > 1 {
        (p.t_end - p.t_start) / (p.samples as f64 - 1.0)
    } else {
        0.0
    };

    let t: Vec<f64> = (0..p.samples)
        .map(|i| p.t_start + i as f64 * dt)
        .collect();

    // Generate signals
    let x1 = generate_x1(&t, p.a1, p.f1, p.phi1);
    let x2 = generate_x2(&t, p.a2, p.f2, p.phi2);

    // Operasi kombinasi
    let y1 = add_signals(&x1, &x2);
    let y2 = subtract_signals(&x1, &x2);
    let y3 = multiply_signals(&x1, &x2);

    let response = SignalResponse { t, x1, x2, y1, y2, y3 };

    HttpResponse::Ok().json(response)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Server berjalan di http://127.0.0.1:8080");
    HttpServer::new(|| {
        App::new()
            .route("/generate", web::post().to(generate_signals))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}