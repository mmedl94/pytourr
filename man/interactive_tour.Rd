% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/interactive_tour.R
\name{interactive_tour}
\alias{interactive_tour}
\title{R wrapper for the interactive_tour function written on python}
\usage{
interactive_tour(data, col_names, plot_objects, half_range, n_max_cols)
}
\arguments{
\item{data}{the dataset you want to investigate}

\item{col_names}{the column names of your dataset}

\item{plot_objects}{a named list of objects you want to be displayed. Each entry requires a definition of
the type of display and a specification of what should be plotted. For tours, a history object, and
for histograms and scatterplots, the names of the variables to be displayed have to be provided (see example).}

\item{half_range}{can be specified directly or be calculated done in the tourr package.}

\item{n_max_cols}{specifies the maximal number of columns of the grid of the final display.}
}
\value{
\itemize{
\item 
}
}
\description{
R wrapper for the interactive_tour function written on python
}
\examples{
library(tourr)
library(devtools)
library(reticulate)
library(pytourr)
f <- apply(flea[,1:6], 2, function(x) (x-mean(x))/sd(x))
guided_tour_history <- save_history(f,
                                   tour_path = guided_tour(holes()))
grand_tour_history <- save_history(f,
                                  tour_path = grand_tour())
tour_history_1d <- save_history(f,
                               tour_path = grand_tour(d=1))

half_range <- max(sqrt(rowSums(f^2)))
col_names <- colnames(f)

init_env()

obj1 <- list(type = "2d_tour", obj = guided_tour_history)
obj2 <- list(type = "1d_tour", obj = tour_history_1d)
obj3 <- list(type = "scatter", obj = c("tars1", "tars2"))
obj4 <- list(type = "hist", obj = "head")

interactive_tour(f,
                col_names,
               list(obj1,obj2,obj3,obj4),
                half_range,
                n_max_cols=2)
}
