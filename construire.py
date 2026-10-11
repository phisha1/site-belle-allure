"""Construit le site Belle Allure dans public/ à partir de catalogue.json et des photos.

Lancer : python3 construire.py
Aperçu  : python3 -m http.server 8000 -d public   puis http://localhost:8000

Pillow seul, pas d'autre dépendance. Le dossier public/ est entièrement refait à chaque fois.
"""
import hashlib
import json
import shutil
from html import escape
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

ICI = Path(__file__).parent
PHOTOS = ICI / "photos"
SRC = ICI / "src"
SORTIE = ICI / "public"

RATIO = 4 / 5  # toutes les photos d'articles en portrait 4:5, comme les boutiques de mode
LARGEURS = (400, 600, 800, 1080)
ANNEE = 2026


# ------------------------------------------------------------------ outils
def prix(n):
    """8000 -> « 8 000 F » avec les espaces insécables de la typographie française."""
    return f"{n:,}".replace(",", " ") + " F"


def e(texte):
    return escape(str(texte), quote=True)


def libelle_tailles(tailles):
    if not tailles:
        return ""
    if len(tailles) == 1:
        return str(tailles[0])
    if all(isinstance(t, int) for t in tailles):
        return f"{tailles[0]} au {tailles[-1]}"
    return f"{tailles[0]} à {tailles[-1]}"


def sur_fond_uni(im, largeur=0.86, hauteur=0.62):
    """Photo détourée sur fond uni (nos chaussures) : on resserre autour de l'objet,
    puis on le pose au centre d'une toile 4:5 du même fond, assez grand pour bien le voir."""
    fond = im.getpixel((2, 2))
    ecart = ImageChops.difference(im, Image.new("RGB", im.size, fond)).convert("L")
    x0, y0, x1, y1 = ecart.point(lambda v: 255 if v > 10 else 0).getbbox()
    marge = 30  # garde le dégradé de l'ombre
    objet = im.crop((max(0, x0 - marge), max(0, y0 - marge), min(im.width, x1 + marge), min(im.height, y1 + marge)))
    W, H = 1080, round(1080 / RATIO)
    k = min(W * largeur / objet.width, H * hauteur / objet.height)
    objet = objet.resize((round(objet.width * k), round(objet.height * k)), Image.LANCZOS)
    toile = Image.new("RGB", (W, H), fond)
    toile.paste(objet, ((W - objet.width) // 2, (H - objet.height) // 2))
    return toile


def recadrer(im, cadrage, ratio=RATIO):
    """Ramène l'image au format voulu (4:5 par défaut).
    Photo sur fond uni (chaussures, cadrage None) : voir sur_fond_uni.
    Photo de mannequin : on coupe, en gardant la hauteur indiquée par cadrage (0 = haut, 1 = bas)."""
    if cadrage is None:
        return sur_fond_uni(im)
    w, h = im.size
    if abs(w / h - ratio) < 0.01:
        return im
    if w / h > ratio:
        nw = round(h * ratio)
        x = round((w - nw) * cadrage)
        return im.crop((x, 0, x + nw, h))
    nh = round(w / ratio)
    y = round((h - nh) * cadrage)
    return im.crop((0, y, w, y + nh))


def decliner(im, base, largeurs=LARGEURS):
    """Enregistre img/<base>-<largeur>.webp pour chaque largeur."""
    for L in largeurs:
        v = im.resize((L, round(L * im.height / im.width)), Image.LANCZOS) if im.width > L else im
        v.save(SORTIE / "img" / f"{base}-{L}.webp", quality=78, method=6)


def ouvrir(chemin):
    return ImageOps.exif_transpose(Image.open(PHOTOS / chemin)).convert("RGB")


def empreinte(*chemins):
    h = hashlib.sha1()
    for c in chemins:
        h.update(c.read_bytes())
    return h.hexdigest()[:8]


# ------------------------------------------------------------------ images
def photo_article(p, chemin):
    im = ouvrir(chemin)
    if "zone" in p:  # [gauche, haut, droite, bas] en fractions : pour zoomer sur le mannequin
        g, h, d, b = p["zone"]
        im = im.crop((round(g * im.width), round(h * im.height), round(d * im.width), round(b * im.height)))
    return recadrer(im, p.get("cadrage"))


def images_articles(produits):
    for p in produits:
        for i, chemin in enumerate(p["photos"], 1):
            im = photo_article(p, chemin)
            decliner(im, f"{p['id']}-{i}")
            if i == 1:  # aperçu des liens partagés (WhatsApp, Facebook)
                im.resize((1080, 1350), Image.LANCZOS).save(SORTIE / "img" / f"{p['id']}-apercu.jpg", quality=80)


def images_rayons(cat, produits):
    """Vignette ronde de chaque catégorie : la photo de son premier article, recadrée en carré."""
    for c in cat["categories"]:
        p = next((q for q in produits if q["categorie"] == c["id"]), None)
        if p:
            im = photo_article(p, p["photos"][0])
            cote = im.width
            y = round((im.height - cote) * (0.5 if p.get("cadrage") is None else 0.2))
            decliner(im.crop((0, y, cote, y + cote)), f"rayon-{c['id']}", (160,))


def images_banniere(boutique):
    im = ouvrir(boutique["photo_accueil"])
    decliner(recadrer(im, 0.35, 3 / 4), "banniere", (400, 700))
    # aperçu 1200x630 pour les liens vers la page d'accueil
    w, h = im.size
    nh = round(w * 630 / 1200)
    y = round((h - nh) * 0.42)
    im.crop((0, y, w, y + nh)).resize((1200, 630), Image.LANCZOS).save(SORTIE / "img" / "accueil-apercu.jpg", quality=80)


def icones():
    logo = Image.open(PHOTOS / "logo.png").convert("RGB")
    for t in (32, 180, 512):
        logo.resize((t, t), Image.LANCZOS).save(SORTIE / f"icone-{t}.png", optimize=True)




# ------------------------------------------------------------------ icônes (trait simple)
def icone(chemins, classe="icone"):
    return f'<svg class="{classe}" viewBox="0 0 24 24" aria-hidden="true">{chemins}</svg>'


I_MESSAGE = icone('<path d="M20 11.5a8 8 0 0 1-11.8 7L4 20l1.5-4.1A8 8 0 1 1 20 11.5z"/>'
                  '<path d="M9.2 9.3c.2 1.9 1.6 3.5 3.5 4.3l.9-.9 1.6.7-.4 1.3c-2.8-.2-5.2-2.6-5.4-5.4l1.3-.4.7 1.6z"/>')
I_MENU = icone('<path d="M4 7h16M4 12h16M4 17h16"/>')
I_FERMER = icone('<path d="M6 6l12 12M18 6L6 18"/>')
I_LOUPE = icone('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>')
I_BILLET = icone('<rect x="3" y="6.5" width="18" height="11" rx="1.5"/><circle cx="12" cy="12" r="2.6"/>'
                 '<path d="M6.5 9.5v5M17.5 9.5v5"/>')
I_CAMION = icone('<path d="M3 7.5h10.5v8.5H3z"/><path d="M13.5 10.5h4l3 3v2.5h-7"/>'
                 '<circle cx="7" cy="17" r="1.7"/><circle cx="17" cy="17" r="1.7"/>')
I_RELAIS = icone('<path d="M4.5 10.5V20h15v-9.5"/><path d="M3 10.5L5 5h14l2 5.5z"/><path d="M10 20v-5h4v5"/>')
I_SAC = icone('<path d="M5.5 8.5h13l-1 11.5h-11z"/><path d="M9 8.5V7a3 3 0 0 1 6 0v1.5"/>')
I_POUBELLE = icone('<path d="M5 7h14M10 7V5h4v2M7 7l1 13h8l1-13"/>')
I_FLECHE = icone('<path d="M5 12h14M13 6l6 6-6 6"/>')
I_COCHE = icone('<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16.5 9.5"/>', "icone merci-icone")


# ------------------------------------------------------------------ morceaux communs
def lien_whatsapp(boutique):
    return f"https://wa.me/{boutique['whatsapp']}" if boutique["whatsapp"] else boutique["facebook"]


def absolue(boutique, chemin):
    return boutique["url"].rstrip("/") + "/" + chemin if boutique["url"] else chemin


def texte_retrait(b):
    """Où se fait le retrait : l'adresse si on la connaît, sinon elle part sur WhatsApp."""
    if b["retrait"]:
        return f"{b['retrait']}. Vous payez en récupérant votre commande."
    return "Nous vous envoyons l'adresse sur WhatsApp. Vous payez en récupérant votre commande."


def tete(boutique, titre, description, racine, apercu, chemin, version, type_og="website"):
    canonique = (f'\n<link rel="canonical" href="{e(absolue(boutique, chemin))}">'
                 f'\n<meta property="og:url" content="{e(absolue(boutique, chemin))}">') if boutique["url"] else ""
    image = absolue(boutique, apercu) if boutique["url"] else racine + apercu
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
<title>{e(titre)}</title>
<meta name="description" content="{e(description)}">
<meta name="theme-color" content="#FFFFFF">
<link rel="icon" href="{racine}icone-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="{racine}icone-180.png">
<meta property="og:type" content="{type_og}">
<meta property="og:site_name" content="{e(boutique['nom'])}">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{e(titre)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{e(image)}">{canonique}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Display:wght@400;500&amp;display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Display:wght@400;500&amp;display=swap"></noscript>
<link rel="stylesheet" href="{racine}style.css?v={version}">
<script src="{racine}commande.js?v={version}" defer></script>
</head>"""


def entete(cat, racine):
    """Comme sur les grands sites (téléphone) : menu et recherche à gauche, logo au centre,
    contact et panier à droite. Sur ordinateur : logo, recherche, contact et panier, catégories dessous."""
    b = cat["boutique"]
    accueil = racine or "./"
    rayons = "".join(f'<li><a href="{accueil}#{c["id"]}">{e(c["nom"])}</a></li>' for c in cat["categories"])
    return f"""<p class="bandeau">Paiement à la réception <span aria-hidden="true">·</span> Retrait gratuit</p>
<header class="entete">
  <div class="entete-ligne">
    <div class="entete-gauche">
      <button type="button" class="entete-icone" data-ouvrir="menu" aria-label="Menu" aria-haspopup="dialog">{I_MENU}</button>
      <button type="button" class="entete-icone entete-loupe" data-basculer-recherche aria-expanded="false" aria-controls="recherche" aria-label="Rechercher">{I_LOUPE}</button>
    </div>
    <a class="marque" href="{accueil}" aria-label="{e(b['nom'])}, accueil">
      <span class="marque-nom">{e(b['nom'])}</span>
      <span class="marque-sous">Boutique</span>
    </a>
    <div class="entete-droite">
      <a class="entete-icone entete-contact" href="{e(lien_whatsapp(b))}" target="_blank" rel="noopener" aria-label="Nous écrire sur WhatsApp">{I_MESSAGE}<span>Nous écrire</span></a>
      <a class="entete-icone entete-panier" href="{racine}panier.html" aria-label="Panier" data-lien-panier>{I_SAC}<span class="entete-libelle">Panier</span><span class="pastille" data-pastille hidden></span></a>
    </div>
    <form class="recherche" id="recherche" action="{accueil}" role="search" data-recherche>
      {I_LOUPE}
      <input type="search" name="q" placeholder="Rechercher un article" aria-label="Rechercher un article" autocomplete="off" enterkeyhint="search">
    </form>
  </div>
  <nav class="entete-rayons" aria-label="Catégories"><ul><li><a href="{accueil}#articles">Tout</a></li>{rayons}</ul></nav>
</header>
<dialog class="menu" id="menu" aria-label="Menu">
  <div class="menu-tete">
    <span class="marque-nom">{e(b['nom'])}</span>
    <button type="button" class="entete-icone" data-fermer aria-label="Fermer le menu">{I_FERMER}</button>
  </div>
  <nav aria-label="Catégories">
    <ul class="menu-liste">
      <li><a href="{accueil}#articles">Tous les articles</a></li>{''.join(f'<li><a href="{accueil}#{c["id"]}">{e(c["nom"])}</a></li>' for c in cat["categories"])}
    </ul>
  </nav>
  <ul class="menu-liste menu-aide">
    <li><a href="{racine}panier.html">Mon panier</a></li>
    <li><a href="{racine}aide.html">Aide : retrait, livraison et paiement</a></li>
    <li><a href="{e(lien_whatsapp(b))}" target="_blank" rel="noopener">Nous écrire sur WhatsApp</a></li>
    <li><a href="{e(b['facebook'])}" target="_blank" rel="noopener">Notre page Facebook</a></li>
  </ul>
</dialog>"""


def pied(cat, racine):
    b = cat["boutique"]
    accueil = racine or "./"
    return f"""<footer class="pied">
  <div class="pied-dedans">
    <div class="pied-marque">
      <p class="marque-nom">{e(b['nom'])}</p>
      <p>{e(b['slogan'])}</p>
    </div>
    <div>
      <h2>Boutique</h2>
      <ul>{''.join(f'<li><a href="{accueil}#{c["id"]}">{e(c["nom"])}</a></li>' for c in cat["categories"])}</ul>
    </div>
    <div>
      <h2>Aide</h2>
      <ul>
        <li><a href="{racine}aide.html#commander">Comment commander</a></li>
        <li><a href="{racine}aide.html#reception">Retrait, livraison et paiement</a></li>
        <li><a href="{racine}aide.html#tailles">Guide des tailles</a></li>
        <li><a href="{racine}aide.html#questions">Questions fréquentes</a></li>
      </ul>
    </div>
    <div>
      <h2>Nous suivre</h2>
      <ul>
        <li><a href="{e(b['facebook'])}" target="_blank" rel="noopener">Facebook</a></li>
        <li><a href="{e(lien_whatsapp(b))}" target="_blank" rel="noopener">WhatsApp</a></li>
      </ul>
    </div>
  </div>
  <p class="pied-petit">© {ANNEE} {e(b['nom'])}</p>
</footer>
</body>
</html>
"""


def garanties(b, classe="garanties"):
    return f"""<ul class="{classe}">
  <li>{I_BILLET}<span>Paiement à la réception</span></li>
  <li>{I_RELAIS}<span>Retrait gratuit en point relais</span></li>
  <li>{I_CAMION}<span>Livraison {prix(b['livraison'])}</span></li>
</ul>"""


def carte(p, racine):
    base = f"{racine}img/{p['id']}-1"
    tailles = libelle_tailles(p["tailles"])
    epuise = p.get("epuise")
    return f"""<li class="carte{' carte-epuisee' if epuise else ''}" data-categorie="{p['categorie']}" data-nom="{e(p['nom'].lower())}">
  <a href="{racine}p/{p['id']}.html">
    <span class="carte-photo">{'<span class="badge">Épuisé</span>' if epuise else ''}<img src="{base}-400.webp" srcset="{base}-400.webp 400w, {base}-600.webp 600w, {base}-800.webp 800w"
      sizes="(min-width: 1024px) 22vw, (min-width: 700px) 31vw, 48vw" width="800" height="1000" loading="lazy" decoding="async" alt=""></span>
    <span class="carte-nom">{e(p['nom'])}</span>
    <span class="carte-prix">{prix(p['prix'])}</span>{f'''
    <span class="carte-tailles">{e(tailles)}</span>''' if tailles and not epuise else ''}
  </a>
</li>"""


def tableau_guide(g):
    tete_ = "".join(f"<th scope=\"col\">{e(c)}</th>" for c in g["colonnes"])
    lignes = "".join("<tr>" + f'<th scope="row">{e(l[0])}</th>' + "".join(f"<td>{e(v)}</td>" for v in l[1:]) + "</tr>"
                     for l in g["lignes"])
    conseils = "".join(f"<li>{e(c)}</li>" for c in g["conseils"])
    unite = f'<p class="guide-unite">{e(g["unite"])}</p>' if g.get("unite") else ""
    return f"""<div class="guide-tableau"><table><thead><tr>{tete_}</tr></thead><tbody>{lignes}</tbody></table></div>
      {unite}
      <h3>Bien mesurer</h3>
      <ul class="guide-conseils">{conseils}</ul>
      <p class="guide-note">Mesures indicatives. En cas de doute, écrivez-nous sur WhatsApp avant de commander.</p>"""


# ------------------------------------------------------------------ pages
def page_accueil(cat, produits, version):
    b = cat["boutique"]
    utilisees = [c for c in cat["categories"] if any(p["categorie"] == c["id"] for p in produits)]
    filtres = "\n".join(
        f'    <button type="button" class="filtre" data-filtre="{c["id"]}" aria-pressed="false">{e(c["nom"])}</button>'
        for c in utilisees)
    rayons = "\n".join(
        f'    <li><a href="#{c["id"]}"><img src="img/rayon-{c["id"]}-160.webp" width="160" height="160" alt="" loading="lazy">'
        f'<span>{e(c["nom"])}</span></a></li>' for c in utilisees)
    cartes = "\n".join(carte(p, "") for p in produits)
    return f"""{tete(b, f"{b['nom']} : robes, chaussures et sacs pour femme", b['description'], '', 'img/accueil-apercu.jpg', '', version)}
<body class="page-accueil">
{entete(cat, '')}
<main>
<section class="banniere">
  <div class="banniere-texte">
    <p class="banniere-surtitre">Nouvel arrivage</p>
    <h1>{e(b['slogan'])}</h1>
    <a class="bouton bouton-clair" href="#articles">Voir les articles {I_FLECHE}</a>
  </div>
  <img class="banniere-photo" src="img/banniere-400.webp" srcset="img/banniere-400.webp 400w, img/banniere-700.webp 700w"
    sizes="(min-width: 860px) 360px, 45vw" width="700" height="933" fetchpriority="high" alt="">
</section>

<nav class="rayons" aria-label="Catégories">
  <ul>
{rayons}
  </ul>
</nav>

{garanties(b)}

<section class="articles" id="articles" aria-labelledby="titre-articles">
  <div class="articles-entete">
    <h2 id="titre-articles">Nos articles</h2>
    <p class="compte"><span data-compte>{len(produits)}</span> articles</p>
  </div>
  <div class="filtres" role="toolbar" aria-label="Filtrer par catégorie" data-filtres>
    <button type="button" class="filtre" data-filtre="tout" aria-pressed="true">Tout</button>
{filtres}
    <span class="filtres-trait" aria-hidden="true"></span>
  </div>
  <p class="vide" data-vide hidden>Aucun article ne correspond à votre recherche. <button type="button" class="lien" data-filtre-tout>Voir tous les articles</button></p>
  <ul class="grille" data-grille>
{cartes}
  </ul>
</section>
</main>
{pied(cat, '')}"""


def balise_photo(p, i, nb, racine):
    base = f"{racine}img/{p['id']}-{i}"
    chargement = 'fetchpriority="high"' if i == 1 else 'loading="lazy"'
    return (f'        <button type="button" class="galerie-photo" data-agrandir="{i - 1}" aria-label="Agrandir la photo {i} sur {nb}">'
            f'<img src="{base}-800.webp" srcset="{base}-400.webp 400w, {base}-600.webp 600w, {base}-800.webp 800w, {base}-1080.webp 1080w" '
            f'sizes="(min-width: 860px) 50vw, 100vw" width="1080" height="1350" {chargement} '
            f'alt="{e(p["nom"])}, photo {i} sur {nb}"></button>')


def visionneuse(p, racine):
    """Photos en plein écran, comme sur les grands sites : on fait glisser, on ferme d'un toucher."""
    nb = len(p["photos"])
    photos = "".join(f'<img src="{racine}img/{p["id"]}-{i}-1080.webp" width="1080" height="1350" loading="lazy" '
                     f'alt="{e(p["nom"])}, photo {i} sur {nb}">' for i in range(1, nb + 1))
    compte = f'<p class="visionneuse-compte" data-visionneuse-compte>1 / {nb}</p>' if nb > 1 else ""
    return f"""<dialog class="visionneuse" id="visionneuse" aria-label="Photos de l'article">
  <button type="button" class="entete-icone visionneuse-fermer" data-fermer aria-label="Fermer">{I_FERMER}</button>
  <div class="visionneuse-piste" data-visionneuse-piste>{photos}</div>
  {compte}
</dialog>"""


def suggestions(p, produits, n=4):
    memes = [q for q in produits if q["categorie"] == p["categorie"] and q is not p and not q.get("epuise")]
    autres = [q for q in produits if q["categorie"] != p["categorie"] and not q.get("epuise")]
    return (memes + autres)[:n]


def page_produit(cat, p, produits, version):
    b = cat["boutique"]
    categorie = next(c for c in cat["categories"] if c["id"] == p["categorie"])
    guide = cat["guides"].get(categorie.get("guide") or "")
    racine = "../"
    nb = len(p["photos"])
    epuise = p.get("epuise")
    photos = "\n".join(balise_photo(p, i, nb, racine) for i in range(1, nb + 1))
    points = ""
    if nb > 1:
        actif = ' aria-current="true"'
        points = '\n      <div class="galerie-points">' + "".join(
            f'<button type="button" data-point="{i}" aria-label="Photo {i + 1}"{actif if i == 0 else ""}></button>'
            for i in range(nb)) + "</div>"
    libelle = categorie["taille"] or "Taille"
    choix = ""
    if p["tailles"] and not epuise:
        epuisees = {str(t) for t in p.get("epuisees", [])}
        dispo = [t for t in p["tailles"] if str(t) not in epuisees]
        seule = len(dispo) == 1 and len(p["tailles"]) == 1
        options = "".join(
            (f'<label class="taille"><input type="radio" name="taille" value="{e(t)}" disabled aria-label="{e(t)}, épuisé">'
             f'<span>{e(t)}</span></label>') if str(t) in epuisees else
            (f'<label class="taille"><input type="radio" name="taille" value="{e(t)}"{" checked" if seule else ""}>'
             f'<span>{e(t)}</span></label>') for t in p["tailles"])
        lien_guide = (f'<button type="button" class="lien-guide" data-ouvrir="guide" aria-haspopup="dialog">{e(guide["titre"])}</button>'
                      if guide else "")
        note = f'<p class="choix-note">Barré : épuisé.</p>' if epuisees else ""
        choix = f"""
      <div class="choix-taille" role="radiogroup" aria-labelledby="titre-taille" data-tailles>
        <div class="choix-tete">
          <p class="choix-titre" id="titre-taille">{libelle} <span class="choix-valeur" data-taille-choisie>{e(p['tailles'][0]) if seule else ''}</span></p>
          {lien_guide}
        </div>
        <div class="tailles">{options}</div>{note}
        <p class="erreur-taille" data-erreur-taille hidden>Choisissez votre {libelle.lower()}.</p>
      </div>"""
    liv = b["livraison"]
    titre = f"{p['nom']} à {prix(p['prix'])} | {b['nom']}"
    aussi = "\n".join(carte(q, racine) for q in suggestions(p, produits))
    if epuise:
        action = f"""
      <button type="button" class="bouton bouton-ajouter" disabled>Épuisé</button>
      <p class="fiche-aide">Cet article est épuisé. <a href="{e(lien_whatsapp(b))}" target="_blank" rel="noopener">Écrivez-nous sur WhatsApp</a> pour être prévenue de son retour.</p>"""
        barre = ""
    else:
        action = f"""
      <button type="button" class="bouton bouton-ajouter" data-ajouter>{I_SAC}Ajouter au panier</button>
      <p class="fiche-aide">Besoin d'aide pour commander ? <a href="{e(lien_whatsapp(b))}" target="_blank" rel="noopener">Écrivez-nous sur WhatsApp</a></p>"""
        barre = f"""
<div class="barre" data-barre>
  <p><span class="barre-nom">{e(p['nom'])}</span><strong>{prix(p['prix'])}</strong></p>
  <button type="button" class="bouton" data-ajouter>Ajouter au panier</button>
</div>"""
    dialogue_guide = f"""
<dialog class="feuille feuille-guide" id="guide" aria-labelledby="titre-guide">
  <div class="feuille-tete">
    <button type="button" class="entete-icone" data-fermer aria-label="Fermer">{I_FERMER}</button>
    <h2 id="titre-guide">{e(guide['titre'])}</h2>
  </div>
  <div class="feuille-corps guide">
      {tableau_guide(guide)}
  </div>
</dialog>""" if guide and p["tailles"] and not epuise else ""
    return f"""{tete(b, titre, p['description'], racine, f"img/{p['id']}-apercu.jpg", f"p/{p['id']}.html", version, 'product')}
<body class="page-fiche">
{entete(cat, racine)}
<main class="fiche" data-produit="{p['id']}" data-taille-libelle="{e(libelle)}">
  <nav class="fil" aria-label="Fil d'Ariane"><a href="{racine}">Accueil</a><span aria-hidden="true">›</span><a href="{racine}#{categorie['id']}">{e(categorie['nom'])}</a></nav>
  <div class="fiche-grille">
    <div class="galerie">
      <div class="galerie-piste" data-piste>
{photos}
      </div>{points}
    </div>
    <div class="fiche-infos">
      <h1>{e(p['nom'])}</h1>
      <p class="fiche-prix">{prix(p['prix'])}</p>
      <p class="fiche-livraison">Retrait gratuit en point relais ou livraison {prix(liv)}. Paiement à la réception.</p>{choix}{action}
      {garanties(b, 'garanties garanties-fiche')}
      <details class="volet" open>
        <summary>Description</summary>
        <p>{e(p['description'])}</p>
      </details>
      <details class="volet">
        <summary>Retrait, livraison et paiement</summary>
        <p><strong>Retrait gratuit en point relais.</strong> {e(texte_retrait(b))}</p>
        <p><strong>Livraison à domicile ou au bureau : {prix(liv)}.</strong> Vous payez au livreur à la réception.</p>
      </details>
    </div>
  </div>

  <section class="aussi" aria-labelledby="titre-aussi">
    <h2 id="titre-aussi">Vous aimerez aussi</h2>
    <ul class="grille">
{aussi}
    </ul>
  </section>
</main>
{barre}
<dialog class="ajoute" id="ajoute" aria-labelledby="titre-ajoute">
  <div class="ajoute-tete">
    <h2 id="titre-ajoute">{I_COCHE}Ajouté au panier</h2>
    <button type="button" class="entete-icone" data-fermer aria-label="Fermer">{I_FERMER}</button>
  </div>
  <div class="feuille-article">
    <img src="{racine}img/{p['id']}-1-400.webp" width="400" height="500" alt="">
    <div>
      <p class="feuille-nom">{e(p['nom'])}</p>
      <p class="feuille-detail" data-detail></p>
      <p class="feuille-prix">{prix(p['prix'])}</p>
    </div>
  </div>
  <a class="bouton" href="{racine}panier.html">Voir le panier et commander</a>
  <button type="button" class="bouton bouton-secondaire" data-fermer>Continuer mes achats</button>
</dialog>{dialogue_guide}
{visionneuse(p, racine)}
{pied(cat, racine)}"""


def page_panier(cat, produits, version):
    """Le panier et la commande sur une seule page, comme les boutiques qui vendent en paiement à la réception."""
    b = cat["boutique"]
    libelles = {c["id"]: c["taille"] or "Taille" for c in cat["categories"]}
    donnees = {p["id"]: {
        "nom": p["nom"], "prix": p["prix"], "image": f"img/{p['id']}-1-400.webp", "lien": f"p/{p['id']}.html",
        "libelle": libelles[p["categorie"]], "tailles": [str(t) for t in p["tailles"]],
        "epuisees": [str(t) for t in p.get("epuisees", [])], "epuise": bool(p.get("epuise")),
    } for p in produits}
    donnees_json = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
    liv = b["livraison"]
    return f"""{tete(b, f"Mon panier | {b['nom']}", b['description'], '', 'img/accueil-apercu.jpg', 'panier.html', version)}
<body class="page-panier">
{entete(cat, '')}
<main class="panier">
  <nav class="fil" aria-label="Fil d'Ariane"><a href="./">Accueil</a><span aria-hidden="true">›</span><span>Panier</span></nav>
  <h1>Mon panier</h1>

  <div class="panier-vide" data-panier-vide hidden>
    {I_SAC}
    <p>Votre panier est vide.</p>
    <a class="bouton" href="./#articles">Voir les articles</a>
  </div>

  <form class="commande-panier" id="commande" novalidate data-panier-formulaire hidden
    data-livraison="{liv}" data-whatsapp="{e(b['whatsapp'])}" data-url="{e(b['url'].rstrip('/'))}">
    <ul class="panier-liste" data-panier-liste></ul>

    <section class="bloc" aria-labelledby="titre-reception">
      <h2 id="titre-reception">Réception</h2>
      <div class="options" role="radiogroup" aria-labelledby="titre-reception">
        <label class="option">
          <input type="radio" name="remise" value="retrait" checked>
          <span class="option-texte">
            <span class="option-titre">{I_RELAIS}Retrait en point relais<em>Gratuit</em></span>
            <span class="option-detail">{e(texte_retrait(b))}</span>
          </span>
        </label>
        <label class="option">
          <input type="radio" name="remise" value="livraison">
          <span class="option-texte">
            <span class="option-titre">{I_CAMION}Livraison à domicile<em>{prix(liv)}</em></span>
            <span class="option-detail">Chez vous ou au bureau. Vous payez au livreur.</span>
          </span>
        </label>
      </div>
    </section>

    <section class="bloc" aria-labelledby="titre-coordonnees">
      <h2 id="titre-coordonnees">Vos coordonnées</h2>
      <div class="champ">
        <label for="c-nom">Votre nom</label>
        <input id="c-nom" name="nom" autocomplete="name" autocapitalize="words" enterkeyhint="next" required aria-describedby="e-nom">
        <p class="champ-erreur" id="e-nom" hidden></p>
      </div>
      <div class="champ">
        <label for="c-tel">Votre numéro</label>
        <div class="champ-tel">
          <span aria-hidden="true">+237</span>
          <input id="c-tel" name="telephone" type="tel" inputmode="tel" autocomplete="tel-national" placeholder="6XX XX XX XX" enterkeyhint="next" required aria-describedby="a-tel e-tel">
        </div>
        <p class="champ-aide" id="a-tel">Pour vous prévenir quand la commande est prête.</p>
        <p class="champ-erreur" id="e-tel" hidden></p>
      </div>
      <div class="champ" data-champ-lieu hidden>
        <label for="c-lieu">Lieu de livraison</label>
        <input id="c-lieu" name="lieu" autocomplete="street-address" autocapitalize="sentences" enterkeyhint="send" aria-describedby="a-lieu e-lieu">
        <p class="champ-aide" id="a-lieu">Ville, quartier et un repère. Par exemple : Yaoundé, Biyem-Assi, près de la pharmacie.</p>
        <p class="champ-erreur" id="e-lieu" hidden></p>
      </div>
    </section>

    <div class="panier-pied">
      <div class="feuille-total">
        <p>À payer à la réception<span data-recap-detail></span></p>
        <strong data-recap-total></strong>
      </div>
      <button type="submit" class="bouton bouton-envoyer">{I_MESSAGE}<span>Commander sur WhatsApp</span></button>
    </div>
  </form>

  <div class="merci merci-page" data-merci hidden>
    {I_COCHE}
    <h2>Dernière étape dans WhatsApp</h2>
    <p>Votre commande est déjà écrite dans WhatsApp. Touchez <strong>Envoyer</strong> pour nous la transmettre. Nous vous répondons pour confirmer.</p>
    <a class="bouton" data-relancer href="#">Rouvrir WhatsApp</a>
    <button type="button" class="bouton bouton-secondaire" data-terminer>C'est envoyé, vider mon panier</button>
  </div>
</main>
<script type="application/json" id="catalogue">{donnees_json}</script>
{pied(cat, '')}"""


def page_aide(cat, version):
    b = cat["boutique"]
    liv = prix(b["livraison"])
    guides = "".join(f"""
    <h3>{e(g['titre'])}</h3>
    <div class="guide">{tableau_guide(g)}</div>""" for g in cat["guides"].values())
    return f"""{tete(b, f"Aide : retrait, livraison et paiement | {b['nom']}", "Comment commander, retrait en point relais, livraison, paiement à la réception, guide des tailles.", '', 'img/accueil-apercu.jpg', 'aide.html', version)}
<body class="page-aide">
{entete(cat, '')}
<main class="aide">
  <nav class="fil" aria-label="Fil d'Ariane"><a href="./">Accueil</a><span aria-hidden="true">›</span><span>Aide</span></nav>
  <h1>Aide</h1>

  <section id="commander" aria-labelledby="titre-commander">
    <h2 id="titre-commander">Comment commander</h2>
    <ol class="etapes">
      <li><span class="etape-num">1</span><p><strong>Choisissez vos articles</strong> et votre taille ou votre pointure, puis touchez « Ajouter au panier ».</p></li>
      <li><span class="etape-num">2</span><p><strong>Ouvrez le panier</strong>, choisissez le retrait gratuit en point relais ou la livraison, et indiquez votre nom et votre numéro.</p></li>
      <li><span class="etape-num">3</span><p><strong>Touchez « Commander sur WhatsApp ».</strong> Votre commande s'écrit toute seule, il ne reste qu'à l'envoyer. Nous vous répondons pour confirmer.</p></li>
    </ol>
  </section>

  <section id="reception" aria-labelledby="titre-reception">
    <h2 id="titre-reception">Retrait, livraison et paiement</h2>
    <p><strong>Retrait gratuit en point relais.</strong> {e(texte_retrait(b))}</p>
    <p><strong>Livraison à domicile ou au bureau : {liv}.</strong> Vous payez au livreur à la réception.</p>
    <p>Dans les deux cas, rien n'est payé sur le site.</p>
  </section>

  <section id="tailles" aria-labelledby="titre-tailles">
    <h2 id="titre-tailles">Guide des tailles</h2>{guides}
  </section>

  <section id="questions" aria-labelledby="titre-questions">
    <h2 id="titre-questions">Questions fréquentes</h2>
    <details class="volet">
      <summary>Faut-il créer un compte ?</summary>
      <p>Non. Votre nom et votre numéro suffisent.</p>
    </details>
    <details class="volet">
      <summary>Puis-je commander plusieurs articles ?</summary>
      <p>Oui. Ajoutez-les au panier : ils partent tous dans un seul message WhatsApp.</p>
    </details>
    <details class="volet">
      <summary>Je ne suis pas sûre de ma taille</summary>
      <p>Regardez le guide des tailles ci-dessus. En cas de doute, écrivez-nous sur WhatsApp avant de commander, on vous conseille.</p>
    </details>
    <details class="volet">
      <summary>Les photos des chaussures sont-elles retouchées ?</summary>
      <p>Nous photographions nous-mêmes nos chaussures. La lumière et le fond ont été arrangés, les chaussures n'ont pas été modifiées.</p>
    </details>
  </section>

  <p class="aide-contact"><a class="bouton" href="{e(lien_whatsapp(b))}" target="_blank" rel="noopener">{I_MESSAGE}Nous écrire sur WhatsApp</a></p>
</main>
{pied(cat, '')}"""


def page_introuvable(cat, version):
    b = cat["boutique"]
    # GitHub Pages sert 404.html à toutes les profondeurs : liens absolus depuis la racine du site
    racine = (b["url"].rstrip("/") + "/") if b["url"] else "/"
    return f"""{tete(b, f"Page introuvable | {b['nom']}", b['description'], racine, 'img/accueil-apercu.jpg', '404.html', version)}
<body class="page-aide">
{entete(cat, racine)}
<main class="aide">
  <h1>Page introuvable</h1>
  <p class="introuvable">Cet article n'est peut-être plus disponible.</p>
  <p class="aide-contact"><a class="bouton" href="{racine}">Voir tous les articles</a></p>
</main>
{pied(cat, racine)}"""


# ------------------------------------------------------------------ assemblage
def construire():
    cat = json.loads((ICI / "catalogue.json").read_text(encoding="utf-8"))
    b = cat["boutique"]
    produits = [p for p in cat["produits"] if b.get("exemples") or not p.get("exemple")]

    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    (SORTIE / "img").mkdir(parents=True)
    (SORTIE / "p").mkdir()

    for f in ("style.css", "commande.js"):
        shutil.copy(SRC / f, SORTIE / f)
    version = empreinte(SRC / "style.css", SRC / "commande.js")

    images_banniere(b)
    images_articles(produits)
    images_rayons(cat, produits)
    icones()

    pages = {
        "index.html": page_accueil(cat, produits, version),
        "panier.html": page_panier(cat, produits, version),
        "aide.html": page_aide(cat, version),
        "404.html": page_introuvable(cat, version),
    }
    pages.update({f"p/{p['id']}.html": page_produit(cat, p, produits, version) for p in produits})
    for chemin, html in pages.items():
        (SORTIE / chemin).write_text(html, encoding="utf-8")

    if b["url"]:
        base = b["url"].rstrip("/")
        urls = [f"{base}/", f"{base}/aide.html"] + [f"{base}/p/{p['id']}.html" for p in produits]
        (SORTIE / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
        (SORTIE / "robots.txt").write_text(f"Sitemap: {base}/sitemap.xml\n", encoding="utf-8")

    poids = sum(f.stat().st_size for f in SORTIE.rglob("*") if f.is_file())
    print(f"{len(produits)} articles, {poids / 1e6:.1f} Mo dans {SORTIE.name}/")
    exemples = [p["nom"] for p in produits if p.get("exemple")]
    if exemples:
        print(f"⚠ {len(exemples)} articles d'exemple affichés (\"exemples\": false pour les retirer) : {', '.join(exemples)}")
    if not b["whatsapp"]:
        print("⚠ Pas de numéro WhatsApp : la commande ouvrira WhatsApp sans destinataire.")
    if not b["retrait"]:
        print("⚠ Pas d'adresse de point relais (retrait) : le site dit qu'elle sera envoyée sur WhatsApp.")
    if not b["url"]:
        print("⚠ Pas d'adresse du site (url) : les aperçus de liens partagés n'auront pas d'image.")


if __name__ == "__main__":
    construire()
