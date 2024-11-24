def generate_waveform_process(audio_file, num_bars, queue):
    """Fonction de processus pour générer la forme d'onde avec librosa."""
    try:
        y, sr = librosa.load(audio_file, sr=None)
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        waveform = rms / np.max(rms)  # Normaliser entre 0 et 1

        # Redimensionner l'onde pour qu'elle ait exactement `num_bars` points
        waveform_resized = np.interp(
            np.linspace(0, len(waveform) - 1, num_bars),
            np.arange(len(waveform)),
            waveform
        )
        queue.put(waveform_resized)  # Met le résultat dans la queue
    except Exception as e:
        print(f"Erreur lors de la génération de la forme d'onde : {e}")
        queue.put([])  # Retourne une liste vide en cas d'erreur


import torchaudio
import torch


def generate_waveform_process(audio_file, num_bars, queue):
    """Fonction de processus pour générer la forme d'onde avec torchaudio."""
    try:
        # Charger le fichier audio
        waveform, sr = torchaudio.load(audio_file)

        # Convertir en mono si nécessaire en prenant la moyenne des canaux
        if waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Calcul RMS
        hop_length = 512
        rms = torch.sqrt(torch.nn.functional.conv1d(waveform ** 2, torch.ones(1, 1, hop_length) / hop_length)).squeeze()

        # Normaliser et redimensionner l'onde
        rms = rms / rms.max() if rms.max() > 0 else rms
        waveform_resized = torch.nn.functional.interpolate(
            rms.unsqueeze(0).unsqueeze(0),
            size=num_bars,
            mode="linear"
        ).squeeze().numpy()

        queue.put(waveform_resized)  # Met le résultat dans la queue
    except Exception as e:
        print(f"Erreur lors de la génération de la forme d'onde : {e}")
        queue.put([])  # Retourne une liste vide en cas d'erreur


from scipy.io import wavfile
import numpy as np
from pydub import AudioSegment


def generate_waveform_process(audio_file, num_bars, queue):
    """Fonction de processus pour générer la forme d'onde avec scipy et numpy, avec gestion des NaN."""
    try:
        # Charger le fichier audio avec pydub pour supporter plusieurs formats
        audio = AudioSegment.from_file(audio_file)

        # Convertir en mono si nécessaire
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Obtenir les données audio sous forme d'onde
        y = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Calcul RMS avec gestion des NaN
        hop_length = 512
        rms = np.sqrt(np.convolve(y ** 2, np.ones(hop_length) / hop_length, mode='valid'))

        # Remplacer les NaN éventuels par 0 ou une petite valeur par défaut
        rms = np.nan_to_num(rms, nan=0.0, posinf=0.0, neginf=0.0)

        # Normaliser et redimensionner l'onde
        if np.max(rms) > 0:
            rms /= np.max(rms)  # Normaliser entre 0 et 1

        waveform_resized = np.interp(
            np.linspace(0, len(rms) - 1, num_bars),
            np.arange(len(rms)),
            rms
        )
        queue.put(waveform_resized)  # Met le résultat dans la queue
    except Exception as e:
        print(f"Erreur lors de la génération de la forme d'onde : {e}")
        queue.put([])  # Retourne une liste vide en cas d'erreur