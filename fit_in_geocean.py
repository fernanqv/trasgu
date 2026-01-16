from chimera_vines import ChimeraVines

# Load configuration from YAML
config = ChimeraVines("geoocean.yaml")

num_chunks = config.get_number_of_chunks()
print(f"Number of chunks: {num_chunks}")
config.fit_vinecop_chunk_parallel(chunk_index=0)



