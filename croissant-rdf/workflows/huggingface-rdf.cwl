cwlVersion: v1.2
class: CommandLineTool
hints:
  DockerRequirement:
    dockerPull: "david4096/croissant-rdf:latest"
inputs:
  fname:
    type: string
    default: huggingface.ttl
  limit:
    type: int
    default: 10
outputs:
  output:
    type: File
    outputBinding:
      glob: $(inputs.fname)
baseCommand: ["/bin/sh", "-c"]
arguments:
  - >
    huggingface-rdf --fname $(inputs.fname) --limit $(inputs.limit)