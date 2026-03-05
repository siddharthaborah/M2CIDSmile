# M2CIDSmile-Tool

**Original Repository:** [https://github.com/Ara198221/M2CIDSmile-Tool](https://github.com/Ara198221/M2CIDSmile-Tool)

Utility tool for fetching PUBCHEM ID and SMILE string form the names of molecules from publicly available molecular database

Abstract:
The importance of making large data set of molecules and to retrieve their smiles strings and molecule ids. The provided R code demonstrates a comprehensive method for obtaining PubChem IDs and canonical SMILES notations for a list of molecules. Utilizing the httr and jsonlite libraries, the code defines a function, get_pubchem_info, that processes each molecule name by making API requests to the PubChem database. This function first retrieves the PubChem CID (Compound Identifier) and then uses this CID to fetch the canonical SMILES string, a standardized representation of the molecule’s structure. The code handles errors gracefully, ensuring that API request failures do not disrupt the entire process. It reads molecule names from an input CSV file, processes each name to gather the necessary chemical information, and combines the results into a unified data frame. Finally, it writes the consolidated data to an output CSV file, facilitating easy analysis and further utilization. This R script is highly useful for researchers and chemists who need to automate the retrieval of molecular identifiers and structures from PubChem. It streamlines the data acquisition process, reduces manual lookup efforts, and ensures data consistency, thereby enhancing productivity and accuracy in chemical informatics studies. For the input file preparation, molecule names should be collected from any public domain database e.g. KNApSAcK (http://www.knapsackfamily.com/KNApSAcK/), IMPPAT (https://cb.imsc.res.in/imppat/basicsearch/phytochemical) etc. and save the file named as molecules.csv. The csv file must contain the molecule names header in the molecule column name as given in readme specifications. 
 


Output:

The code will generate an output file with Pubchem ID and Smiles a

 


******** Enjoy the tool for basic research********
