# This is a sample Python script.

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.




import os
import numpy as np
from preprocessing.metadata_processing import metadata_processing
from preprocessing.peak_processing import peak_processing
from matchms import calculate_scores
from matchms.similarity import CosineGreedy
from matchms.importing import load_from_mgf, load_from_msp
from matchms.similarity import ModifiedCosine
from IO.out import plotScores
from IO.out import plotScoresRestrictive
from IO.out import getBestMatches
from IO.out import generateNetwork
import time
import gensim
from spec2vec import Spec2Vec
from spec2vec import SpectrumDocument
from spec2vec.model_building import train_new_word2vec_model
from matchms.importing import load_from_json
import pyperf
from ms2deepscore import MS2DeepScore
from ms2deepscore.models import load_model



#TUTORIAL 1 modified cosine vs cosine greedy

similarity_measure = ModifiedCosine(tolerance=0.005)
path_data = "C:/Users/migue/OneDrive/Escritorio/GSOC/vector_db"  # enter path to downloaded mgf file
file_mgf = os.path.join(path_data, 
                        "GNPS-NIH-NATURALPRODUCTSLIBRARY.mgf")
spectrums = list(load_from_mgf(file_mgf))
spectrums = [metadata_processing(s) for s in spectrums]
spectrums = [peak_processing(s) for s in spectrums]
start_time = time.time()
scores = calculate_scores(spectrums, spectrums, similarity_measure, is_symmetric=True)
scores_array = scores.scores
min_match = 5
plotScoresRestrictive(scores_array, min_match)
modified_cosine = time.time()
modified_cosine_time = modified_cosine - start_time
similarity_measure = CosineGreedy(tolerance=0.005)
scores = calculate_scores(spectrums, spectrums, similarity_measure, is_symmetric=True)
getBestMatches(scores, spectrums, 5, 10)
cosine_greedy = time.time()
cosine_greedy_time = cosine_greedy-modified_cosine
print("Modified cosine time:", modified_cosine_time, "seconds")
print("Cosine greedy time:", cosine_greedy_time, "seconds")

#TUTORIAL 2 Spec2Vec


path_data = "C:/Users/migue/OneDrive/Escritorio/GSOC/vector_db"
file_mgf = os.path.join(path_data, "GNPS-NIH-NATURALPRODUCTSLIBRARY.mgf")
spectrums = list(load_from_mgf(file_mgf))
spectrums = [metadata_processing(s) for s in spectrums]
spectrums = [peak_processing(s) for s in spectrums]
spectrum_documents = [SpectrumDocument(s, n_decimals=2) for s in spectrums]
model_file = "tutorial_model.model"
model = train_new_word2vec_model(spectrum_documents, iterations=[25], filename=model_file, workers=2, progress_logger=True)
spec2vec_similarity = Spec2Vec(model=model, intensity_weighting_power=0.5, allowed_missing_percentage=5.0)
scores = calculate_scores(spectrums, spectrums, spec2vec_similarity, is_symmetric=True)
getBestMatches(scores, spectrums, 11, 10)



#TUTORIAL 3 Networking

path_data = "C:/Users/migue/OneDrive/Escritorio/GSOC/vector_db"
file_mgf = os.path.join(path_data, "GNPS-NIH-NATURALPRODUCTSLIBRARY.mgf")
spectrums = list(load_from_mgf(file_mgf))
spectrums = [metadata_processing(s) for s in spectrums]
spectrums = [peak_processing(s) for s in spectrums]
path_model = os.path.join(os.path.dirname(os.getcwd()), "vector_db")
filename_model = "spec2vec_AllPositive_ratio05_filtered_201101_iter_15.model"
filename = os.path.join(path_model, filename_model)
model = gensim.models.Word2Vec.load(filename)
spec2vec_similarity = Spec2Vec(model=model, intensity_weighting_power=0.5, allowed_missing_percentage=5.0)
scores = calculate_scores(spectrums, spectrums, spec2vec_similarity, is_symmetric=True)
generateNetwork(scores, spectrums)


#TUTORIAL 4 ms2deepscore
path_data = "C:/Users/migue/OneDrive/Escritorio/GSOC/vector_db"
file_mgf = os.path.join(path_data, "GNPS-NIH-NATURALPRODUCTSLIBRARY.mgf")
spectrums = list(load_from_mgf(file_mgf))
spectrums = [metadata_processing(s) for s in spectrums]
spectrums = [peak_processing(s) for s in spectrums]
model = load_model("MS2DeepScore_allGNPSpositive_10k_500_500_200.hdf5")
similarity_measure = MS2DeepScore(model)
scores = calculate_scores(spectrums, spectrums, similarity_measure, is_symmetric=True)
scores_array = scores.scores.to_array()
getBestMatches(scores, spectrums, 5, 10)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
