source("install_packages.R")

# Now load all the packages
invisible(lapply(required_packages, library, character.only = TRUE))

# Add this line at the beginning of your server.R script
cat("Current working directory is:", getwd(), "\n")

# Load necessary libraries
library(shiny)
library(httr)
library(jsonlite)

# Define UI for the application
ui <- fluidPage(
    titlePanel("Molecule Information Fetcher"),
    
    sidebarLayout(
        sidebarPanel(
            fileInput("file1", "Choose CSV File",
                      accept = c("text/csv",
                                 "text/comma-separated-values,text/plain",
                                 ".csv")),
            actionButton("process", "Process Molecules"),
            downloadButton("downloadData", "Download Output")
        ),
        
        mainPanel(
            tableOutput("contents")
        )
    )
)

# Define server logic required to fetch PubChem data
server <- function(input, output, session) {
    
    get_pubchem_info <- function(molecule_name) {
        # URL encode the molecule name
        encoded_name <- URLencode(molecule_name, reserved = TRUE)
        
        # Construct URL to fetch PubChem CID
        url_cid <- paste0("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/", encoded_name, "/cids/JSON")
        
        # Fetch PubChem CID
        response_cid <- tryCatch(GET(url_cid), error = function(e) NULL)
        
        if (!is.null(response_cid) && status_code(response_cid) == 200) {
            content_cid <- content(response_cid, "parsed")
            pubchem_cid <- content_cid$IdentifierList$CID[1]
            
            if (!is.null(pubchem_cid)) {
                # Construct URL to fetch canonical SMILES using CID
                url_smiles <- paste0("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/", pubchem_cid, "/property/CanonicalSMILES/JSON")
                
                # Fetch SMILES
                response_smiles <- tryCatch(GET(url_smiles), error = function(e) NULL)
                
                if (!is.null(response_smiles) && status_code(response_smiles) == 200) {
                    content_smiles <- content(response_smiles, "parsed")
                    # PubChem may return the field as CanonicalSMILES or ConnectivitySMILES
                    smiles <- content_smiles$PropertyTable$Properties[[1]]$CanonicalSMILES
                    if (is.null(smiles)) {
                        smiles <- content_smiles$PropertyTable$Properties[[1]]$ConnectivitySMILES
                    }
                    
                    if (!is.null(smiles)) {
                        return(data.frame(CID = pubchem_cid, Molecule = molecule_name, SMILES = smiles, stringsAsFactors = FALSE))
                    }
                }
            }
        }
        
        return(data.frame(CID = NA, Molecule = molecule_name, SMILES = NA, stringsAsFactors = FALSE))
    }
    
    # Reactive value to store results
    results <- reactiveVal(NULL)
    
    observeEvent(input$process, {
        req(input$file1)
        inFile <- input$file1
        
        molecule_data <- tryCatch(read.csv(inFile$datapath, stringsAsFactors = FALSE), error = function(e) NULL)
        
        if (is.null(molecule_data)) {
            showNotification("Error reading input file.", type = "error")
            return(NULL)
        }
        
        molecule_names <- molecule_data$molecule
        
        if (is.null(molecule_names) || length(molecule_names) == 0) {
            showNotification("No molecule names found in the input file.", type = "error")
            return(NULL)
        }
        
        results_list <- lapply(molecule_names, get_pubchem_info)
        
        # Ensure column names are consistent for all data frames
        consistent_names <- c("CID", "Molecule", "SMILES")
        results_list <- lapply(results_list, function(df) {
            colnames(df) <- consistent_names
            return(df)
        })
        
        # Combine results into a single data frame
        results_df <- do.call(rbind, results_list)
        
        results(results_df)
    })
    
    output$contents <- renderTable({
        req(results())
        results()
    })
    
    output$downloadData <- downloadHandler(
        filename = function() {
            "molecule-output.csv"
        },
        content = function(file) {
            write.csv(results(), file, row.names = FALSE)
        }
    )
}

# Run the application 
shinyApp(ui = ui, server = server)
