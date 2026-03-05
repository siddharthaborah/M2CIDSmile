# install_packages.R
required_packages <- c("shiny", "httr", "jsonlite")

check_and_install_packages <- function(packages) {
  for (pkg in packages) {
    if (!require(pkg, character.only = TRUE)) {
      cat(paste("Package", pkg, "not found. Installing now...\n"))
      install.packages(pkg, dependencies = TRUE)
      if (!require(pkg, character.only = TRUE)) {
        stop(paste("Package", pkg, "could not be installed."))
      } else {
        cat(paste("Package", pkg, "successfully installed and loaded.\n"))
      }
    } else {
      cat(paste("Package", pkg, "is already installed and loaded.\n"))
    }
  }
}

check_and_install_packages(required_packages)
