from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import basicsynbio as bsb
import json

from starlette.responses import FileResponse
from app.schema import (
    fileType,
    fileTypeData,
    basicAssembly,
    basicPart,
    responseCollectionsName,
    responseCollectionsData,
    responseMultipleFileUpload,
    responseSingularFileUpload,
    responseValidate,
    responseViewSeqLabels,
)
from typing import List, Optional

from app.src.getCollections import getCollections
from app.src.fileUploadSingular import fileUploadSingular
from app.src.fileUploadMultiple import fileUploadMultiple
from app.src.buildCSVs import buildCSVs
from app.src.buildEchoInstructions import buildEchoInstructions
from app.src.buildPDFInstructions import buildPDFInstructions
from app.src.buildJSON import buildJSON
from app.src.buildUniqueParts import buildUniqueParts
from app.src.buildUniqueAssemblies import buildUniqueAssemblies
from app.src.validateAssembly import validateAssembly
from app.src.viewAssemblySeq import return_assembly_sequence
from app.src.viewseqlabels import viewseqlabels
from app.src.viewpartlabels import viewpartlabels
from app.src.return_sequence_annotations import return_sequence_annotations
from app.src.dnafeatureviewer import dnafeaturesviewerpng
from app.src.dnafeatureviewer_assembly import dnafeaturesviewerpng_assembly
from app.utils.createHashFileDictionary import createHashFileDictionary

description = """
A REST API for BasicSynBio that allows the BasicSynBio python package to be consumed by any language - the primary use case for this is own own BasicSynBio frontend application. 🚀

[Python Package](https://pypi.org/project/basicsynbio/) --- 
[Interactive Web App](https://basicsynbio.web.app)

Below is a list of endpoints that can be accessed via the API, each endpoint can be simulated within their corresponding boxes.
"""

app = FastAPI(
    title="BasicSynBio API", description=description, version="0.0.1", debug=True
)

origins = [
    "http://basicsynbio.web.app",
    "https://basicsynbio.web.app",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# the `/docs` endpoint is reserved for OPENAPI good for testing
# Root to the API to check if it is running ^^^
@app.get("/")
def root_endpoint_for_health_check():
    """
    ## API Root

    Root endpoint for health check, returns basic message.
    """
    return {"message": "Hello World"}


# Route to return a list of all the available collections ^^^
@app.get("/collections/names", response_model=responseCollectionsName)
def get_collection_names():
    """
    ## Collection Names

    Returns a list of the available basicynbio part collections to the user.

    More infomation about part linker collections can be found at the [basicsynbio documentation](https://londonbiofoundry.github.io/basicsynbio/collections.html)
    """
    return {"data": [x for x in dir(bsb) if x.startswith("BASIC_")]}


# Route to return data as a dictionary within available collections ^^^
@app.get("/collections/data", response_model=responseCollectionsData)
def get_collection_data():
    """
    ## Collection Data

    Returns a list of the available basicynbio part collections and the data within them to the user.

    More infomation about part linker collections can be found at the [basicsynbio documentation](https://londonbiofoundry.github.io/basicsynbio/collections.html)
    """
    return {"data": getCollections()}


# Route to return the json basic part witin a uploaded file ^^^
@app.post("/fileupload/singular", response_model=responseSingularFileUpload)
def singular_file_upload(type: fileType, addiseq: bool, file: UploadFile = File(...)):
    """
    ## Singular File Upload

    Uploads a file containing only one sequence record to the server to return a JSON version of the same object for further processing in the basicsynbio interactive web app.
    """
    return fileUploadSingular(type, addiseq, file)


# Route to return the json basic part for each record within a uploaded file ^^^
@app.post("/fileupload/multiple", response_model=responseMultipleFileUpload)
async def multiple_file_upload(
    type: fileType, addiseq: bool, file: UploadFile = File(...)
):
    """
    ## Multiple File Upload

    Uploads a file containing more than one sequence record to the server to return a JSON version of the same object for further processing in the basicsynbio interactive web app.
    """
    return await fileUploadMultiple(type, addiseq, file)


# Route to return unique assemblies genbank representation on basicAssembly Object ^^^
@app.post("/validate", response_model=responseValidate)
async def validate_assembly(
    myPartArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    """
    ## Validate

    This endpoint ensures that a input list of basicParts can successfully build a basic assembly.
    """
    PartArray = json.loads(myPartArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return validateAssembly(PartArray, hashFileDictionary)


# Route to return CSV representation on basicAssembly Object ^^^
@app.post("/buildcsvs", response_class=FileResponse)
async def build_csvs(
    background_tasks: BackgroundTasks,
    myAssemblyArrayStr: str = Form(...),
    files: Optional[List[UploadFile]] = File([]),
):
    """
    ## Build CSVs

    This endpoint takes a list of basicAssembly objects and returns a CSV representation of the same objects.
    """
    AssemblyArray = json.loads(myAssemblyArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return buildCSVs(
        assemblyArray=AssemblyArray,
        hashFileDict=hashFileDictionary,
        background_tasks=background_tasks,
    )


# Route to return echo representation on basicAssembly Object
@app.post("/buildechoinstructions")
async def build_echo_instructions(
    myAssemblyArrayStr: str = Form(...),
    files: Optional[List[UploadFile]] = File([]),
):
    """
    ## Build Echo Instructions

    This endpoint takes a list of basicAssembly objects and returns the Echo robot instructions to perform the clip step of BASIC DNA assembly.
    """
    AssemblyArray = json.loads(myAssemblyArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return buildEchoInstructions(
        assemblyArray=AssemblyArray,
        hashFileDict=hashFileDictionary,
    )


# Route to return PDF representation on basicAssembly Object
@app.post("/build_pdf_instructions")
async def build_pdf_instructions(
    myAssemblyArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    """
    ## Build PDF Instructions

    This endpoint takes a list of basicAssembly objects and returns a PDF for the manual assembly within a lab of the basicAssembly object.
    """
    AssemblyArray = json.loads(myAssemblyArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return buildPDFInstructions(AssemblyArray, hashFileDictionary)


# Route to return JSON representation on basicAssembly Object
@app.post("/buildjson")
async def build_json(
    myAssemblyArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    """
    ## Build JSON

    This endpoint takes a list of basicAssembly objects and returns a JSON serialised version of the same objects.
    """
    AssemblyArray = json.loads(myAssemblyArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return buildJSON(AssemblyArray, hashFileDictionary)


# Route to return unique assemblies genbank representation on basicAssembly Object
@app.post("/builduniqueparts")
async def build_unique_parts_as_genbank(
    myAssemblyArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    """
    ## Build Unique Parts

    This endpoint takes a list of basicAssembly objects and returns unique parts within each BasicAssembly as a genbank file.
    """
    AssemblyArray = json.loads(myAssemblyArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return buildUniqueParts(AssemblyArray, hashFileDictionary)


# Route to return unique assemblies genbank representation on basicAssembly Object
@app.post("/builduniqueassemblies")
async def buils_unique_assemblies_as_genbank(
    myAssemblyArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    """
    ## Build Unique Assemblies

    This endpoint takes a list of basicAssembly objects and returns unique assemblies within the basicAssembly as a genbank file.
    """
    AssemblyArray = json.loads(myAssemblyArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return buildUniqueAssemblies(AssemblyArray, hashFileDictionary)


#################### Visualization ####################

# Route to return unique assemblies seq labels representation of basicAssembly Object
@app.post("/viewseqlabels", response_model=responseViewSeqLabels)
async def view_sequence_labels(
    myPartArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    PartArray = json.loads(myPartArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return viewseqlabels(PartArray, hashFileDictionary)


# Route to return unique assemblies part labels representation of basicAssembly Object
@app.post("/viewpartlabels", response_model=responseViewSeqLabels)
async def view_part_labels(
    myPart: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    jsonPart = json.loads(myPart)
    hashFileDictionary = createHashFileDictionary(files)
    return viewpartlabels(jsonPart, hashFileDictionary)


# Route to return sequence annotations
@app.post("/returnseqann", response_model=responseViewSeqLabels)
async def view_sequence_annotations(
    Qualifier: str = Form(...),
    myPart: str = Form(...),
    files: Optional[List[UploadFile]] = File([]),
):
    jsonPart = json.loads(myPart)
    hashFileDictionary = createHashFileDictionary(files)
    return return_sequence_annotations(jsonPart, Qualifier, hashFileDictionary)


@app.post("/assemblySeq", response_model=responseViewSeqLabels)
async def return_assembly_seq_and_annotations(
    Qualifier: str = Form(...),
    myPartArrayStr: str = Form(...),
    files: Optional[List[UploadFile]] = File([]),
):
    PartArray = json.loads(myPartArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return return_assembly_sequence(
        parts=PartArray, Qualifier=Qualifier, hashFileDictionary=hashFileDictionary
    )


# Route to return sequence annotations
@app.post("/dnafeatureviewer")
async def dnafeatureviewer(
    myPart: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    jsonPart = json.loads(myPart)
    hashFileDictionary = createHashFileDictionary(files)
    return dnafeaturesviewerpng(jsonPart, hashFileDictionary)


# Route to return sequence annotations for assemblys on Dna feature viewer
@app.post("/dnafeatureviewer_assembly")
async def dnafeaturesviewer_for_assemblies(
    myPartArrayStr: str = Form(...), files: Optional[List[UploadFile]] = File([])
):
    PartArray = json.loads(myPartArrayStr)
    hashFileDictionary = createHashFileDictionary(files)
    return dnafeaturesviewerpng_assembly(PartArray, hashFileDictionary)
