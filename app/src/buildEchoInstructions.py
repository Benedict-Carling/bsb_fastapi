from typing import Dict, List
from app.schema import basicAssembly
from app.utils.jsonAssemblyArrayToBsbBuild import jsonAssemblyArrayToBsbBuild

from app.utils.readReturnDelete import (
    create_file_execute_build_command_return,
    read_return_delete,
    returnFileResponse,
)

import basicsynbio as bsb


def buildEchoInstructions(
    assemblyArray: List[basicAssembly], hashFileDict: Dict = None
):
    try:
        bsbBuild = jsonAssemblyArrayToBsbBuild(assemblyArray, hashFileDict)
        if isinstance(bsbBuild, str):
            return {"result": False, "message": bsbBuild}
        filepath = bsb.export_echo_assembly_instructions(bsbBuild)
        return read_return_delete(filepath, "application/zip", filepath)

    except Exception as e:
        return {"result": False, "message": str(e)}
