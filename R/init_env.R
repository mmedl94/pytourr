init_env <- function(env_name="r-pytourr"){
  # Check if python is available
  reticulate::py_available(initialize = FALSE)
  # check if python environment exists and create new one if not
  if (env_name %in% reticulate::conda_list()$name==FALSE){
    reticulate::conda_create(env_name)
  }
  # initialize python environment
  reticulate::use_condaenv(env_name)

  # check if required packages are installed and install them if not
  package_names <- reticulate::py_list_packages(envname = env_name)
  required_packages <- c("pandas", "numpy", "matplotlib")
  for (package in required_packages){
    if (package %in% package_names$package==FALSE){reticulate::conda_install(env_name, package)}
  }
  base::cat(base::sprintf('Python environment "%s" successfully loaded', env_name), "\n")

  # Check accessibility of python functions
  pytourr_dir <- find.package("pytourr", lib.loc=NULL, quiet = TRUE)
  check_dir <- base::paste(pytourr_dir,"/python/check_pytour.py", sep = "")
  reticulate::source_python(check_dir)
  reticulate::py$check_pytour()
}