# This is a sample Python script.

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.




import numpy as np
from IO.export import generateNetwork
from IO.importing import loadScpectrums
from IO.importing import importSpec2VecModel
from IO.importing import importMS2DeepscoreModel
from IO.importing import read_mgf
from preprocessing.metadata_processing import metadata_processing
from preprocessing.peak_processing import peak_processing
from preprocessing.train_spec2vec import train_spec2vec
from preprocessing.binPeakList import bin_peak_list
from preprocessing.get_Spec2Vec_vectors import get_Spec2Vec_vectors
from vectorization.reshape_vectors import reshape_vectors
from vectorization.create_IndexFlatL2 import create_IndexFlatL2
from vectorization.create_IndexFlatIP import create_IndexFlatIP
from vectorization.create_IndexIVFFlat import create_IndexIVFFlat
from vectorization.create_IndexLSH import create_IndexLSH
from vectorization.create_IndexHNSWFlat import create_IndexHNSWFlat
from vectorization.create_IndexIVFScalarQuantizer import create_IndexIVFScalarQuantizer
from vectorization.create_IndexIVFPQ import create_IndexIVFPQ
from vectorization.create_IndexIVFPQR import create_IndexIVFPQR
from vectorization.create_IndexPQ import create_IndexPQ
from vectorization.create_IndexScalarQuantizer import create_IndexScalarQuantizer
from vectorization.simple_vectorization import simple_vectorization
from vectorization.simple_vectorization2 import simple_vectorization2
from vectorization.create_MilvusEntities import create_MilvusEntities
from vectorization.create_MilvusCollection import create_MilvusCollection
from vectorization.create_MilvusIndexIVFFlat import create_MilvusIndexIVFFlat
from vectorization.create_MilvusIVFSP import create_MilvusIVFSP
from vectorization.create_MilvusIndexHNSW import create_MilvusIndexHNSW
from vectorization.create_MilvusIndexANNOY import create_MilvusIndexANNOY
from vectorization.create_MilvusIndexIVFSQ8 import create_MilvusIndexIVFSQ8
from vectorization.create_MilvusIndexFlat import create_MilvusIndexFlat
from vectorization.create_MilvusFlatSP import create_MilvusFlatSP
from vectorization.create_MilvusIndexIVFPQ import create_MilvusIndexIVFPQ
from comparison.cosine_greedy import cosine_greedy
from comparison.modified_cosine import modified_cosine
from comparison.spec2vec import spec2vec
from comparison.ms2deepscore import ms2deepscore
from visualization.plot_scores_restrictive import plotScoresRestrictive
from visualization.plot_scores import plotScores
from visualization.get_best_matches import getBestMatches
from statistics.export_benchmarking import export_benchmarking
import time
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)
import logging
import yaml
import subprocess
import os


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
with open('indexesConfig.yaml', 'r') as file:
    yaml_data = yaml.safe_load(file)

def remove_random(peaks, remove_n=2):
    remove_indexes = np.random.randint(0, len(peaks[0]), remove_n)
    peaks = np.delete(peaks, remove_indexes, 1)
    peaks[1] = peaks[1] * (1.15 - 0.30 * np.random.random_sample(len(peaks[0])))
    return peaks
def argsort(*arrays):
    indexes = arrays[0].argsort()
    return tuple((a[indexes] for a in arrays))

def indexSearch(vectors_array, yaml_data):
    index_type = yaml_data['index']
    if (yaml_data['mode'] == "faiss"):
        if index_type in yaml_data['faiss_indexes']:
            function_name = yaml_data['faiss_indexes'][index_type]['function']
            if function_name in globals():
                selected_function = globals()[function_name]
            if 'param2' in yaml_data['faiss_indexes'][index_type]:
                param1 = yaml_data['faiss_indexes'][index_type]['param1']
                param2 = yaml_data['faiss_indexes'][index_type]['param2']
                index = selected_function(vectors_array, param1, param2)
            elif 'param1' in yaml_data['faiss_indexes'][index_type]:
                param1 = yaml_data['faiss_indexes'][index_type]['param1']
                index = selected_function(vectors_array, param1)
            else:
                index = selected_function(vectors_array)
        D, I = index.search(vectors_array[:5], 4)
        print(D)
        print(I)
    elif (yaml_data['mode'] == "milvus"):
        search_type = yaml_data['search_params_type']
        command = ["sudo", "docker-compose", "up", "-d"]
        subprocess.run(command)
        time.sleep(60)
        connections.connect("default", host="localhost", port="19530")
        entities = create_MilvusEntities(vectors_array[:100])
        milvus_vectors = create_MilvusCollection(vectors_array[:100], entities)
        if search_type in yaml_data['search_parameters']:
            function_name = yaml_data['search_parameters'][search_type]['function']
            metric_type = yaml_data['metric_type']
            if function_name in globals():
                selected_function = globals()[function_name]

            if 'param1' in yaml_data['search_parameters'][search_type]:
                param1 = yaml_data['search_parameters'][search_type]['param1']
                search_params = selected_function(metric_type, param1)
            else:
                search_params = selected_function(metric_type)
            function_name = yaml_data['milvus_indexes'][index_type]['function']
            if function_name in globals():
                selected_function2 = globals()[function_name]
            if 'param1' in yaml_data['milvus_indexes'][index_type]:
                param1 = yaml_data['milvus_indexes'][index_type]['param1']
                milvus_vectors = selected_function2(milvus_vectors, metric_type, param1)
            else:
                milvus_vectors = selected_function2(milvus_vectors, metric_type)
            milvus_vectors.load()
            vectors_to_search = entities[-1][-2:]
            result = milvus_vectors.search(vectors_to_search, "embeddings", search_params, limit=3,
                                           output_fields=["pk"])
            milvus_vectors.release()
            milvus_vectors.drop_index()
            """command = ["sudo", "docker-compose", "down"]
            subprocess.run(command)
            command = ["sudo", "rm", "-rf", "volumes"]
            subprocess.run(command)"""
            return result

start_time = time.time()
# lib1 = r"D:\Data\lib\BILELIB19.mgf"


lib1 = os.path.abspath('GNPS-NIH-NATURALPRODUCTSLIBRARY.mgf')

libname = "gnps"
model_file= "New model2"
#  use 11 as min mz as we are also using it for neutral losses
"""min_mz = 11
max_mz = 1500
logger.info("Read mgf")
spec_df = read_mgf(lib1, 4, max_mz, 0.001)
logger.info("read done; create vectors for {}".format(spec_df.shape[0]))
spec_df["npeaks"] = [len(peaks[1]) for peaks in spec_df["peaks"]]
spec_df["max_i"] = [peaks[1].max() for peaks in spec_df["peaks"]]
spec_df["sum_i"] = [peaks[1].sum() for peaks in spec_df["peaks"]]
spec_df["sum_by_max"] = spec_df["sum_i"] / spec_df["max_i"]
spec_df = spec_df.sort_values(by="sum_by_max", ascending=False).reset_index()
spec_df.to_csv(f"{libname}_calc.csv")"""
spectra = loadScpectrums(lib1)
spectra = [peak_processing(spectrum) for spectrum in spectra]
#spectra = [metadata_processing(spectrum) for spectrum in spectra]
model = train_spec2vec(model_file,spectra)
vectors_array= get_Spec2Vec_vectors(model)
#vectors_array = np.array([bin_peak_list(peaks, min_mz, max_mz, 0.05, precursor, include_neutral_loss=True) for
                       #precursor, peaks in zip(spec_df["precursor_mz"], spec_df["peaks"])], dtype="float32")
result= indexSearch(vectors_array,yaml_data)
print(result)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
