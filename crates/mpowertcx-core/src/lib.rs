pub mod converter;
pub mod equipment;
pub mod physics;
pub mod ride;
pub mod tcx;

pub use converter::{ConvertOptions, Converter};
pub use ride::{python_float, Ride, RideHeader};

pub const VERSION: &str = "2.1.0";
