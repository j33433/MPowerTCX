pub mod converter;
pub mod equipment;
pub mod fit_out;
pub mod linter;
pub mod physics;
pub mod ride;
pub mod tcx;

pub use converter::{ConvertOptions, Converter};
pub use linter::{lint_tcx, has_errors, LintResult, Severity};
pub use ride::{python_float, Ride, RideHeader};

pub const VERSION: &str = "2.1.0";
