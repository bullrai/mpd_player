# app/utils/helpers.py

def handle_mpd_error(error):
    """Affiche un message d'erreur pour les exceptions liées à MPD."""
    print(f"Erreur MPD : {error}")

def format_time(seconds):
    """Formate une durée en secondes sous forme de minutes:secondes."""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02}"

def format_track_info(track):
    """Formate les informations de piste pour l'affichage."""
    title = track.get("title", "Titre inconnu")
    artist = track.get("artist", "Artiste inconnu")
    album = track.get("album", "Album inconnu")
    return f"{title} - {artist} | {album}"
