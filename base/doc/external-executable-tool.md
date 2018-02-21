External executable tool
--------------------------

To wrap an existing executable in the pipeline you need to do the following:

  1. Create a new container directory (e.g. `container/example` )
  
  2. Create a `tool.yml` file in the container directory such as the following:
      
         entry_point: "bonseyes_containers.external_executable_tool:create_external_executable_tool"
         description: "Example tool"
         command: "/app/test.sh"
         parameters:
           parameter1:
             type: "artifact"
             label: "Parameter 1"
             artifact-type: com.bonseyes.example.some_artifact_type
           string_param:
             type: "string"
             label: "String param"
           file_param:
             type: "file"
             label: "File param"
         output_type: com.bonseyes.example.some_other_type
        
     Change the command, parameters and output_type parameters to something appropriate to your situation
     
  3. Create a Dockerfile in the container directory such as the following:
  
         FROM bonseyes-base
         ADD containers/test2 /app
         
     You can adapt the container to suit your needs such as adding more libraries.
 
You can now test your container with a the bonseyes_client tool with a command as the following:

    python3 -m bonseyes_client run  -f containers/example/Dockerfile --output-file out.dat \
            --parameters '{"parameter1": "xxxxx", "string_param": "yyyy"}' \
            --input-file file_param=input_file.dat
