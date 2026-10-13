# Site Belle Allure

Boutique en ligne de mode femme : robes, chaussures, sacs, pagne.
La disposition reprend celle des grands sites de vente (Zara, Jumia) : en-tête fixe avec menu,
recherche et contact, bannière, catégories, garanties, grille d'articles.

Pensé d'abord pour le téléphone. Sur la fiche d'un article, la cliente choisit sa taille et touche
« Commander ». Un volet plein écran s'ouvre : nom, numéro (+237 déjà mis), lieu de livraison,
quantité ; le total et le bouton restent visibles en bas, même clavier ouvert. Les erreurs
s'affichent sous le champ concerné. « Envoyer sur WhatsApp » ouvre WhatsApp avec la commande déjà
écrite ; au retour, un écran rappelle de toucher « Envoyer » dans WhatsApp. Les photos s'agrandissent
d'un toucher. Paiement à la livraison, sans compte ni panier.
La page `aide.html` explique la commande, la livraison et le paiement.

Site statique (HTML, CSS, un peu de JavaScript), sans bibliothèque, pour rester léger
sur les connexions lentes.

## En ligne

Le site est hébergé sur Vercel : https://belle-allure-iota.vercel.app
Chaque `git push` sur `main` le reconstruit et le republie (réglages dans `vercel.json`).

## Organisation

| Fichier | Rôle |
|---|---|
| `catalogue.json` | **Le seul fichier à modifier au quotidien** : réglages de la boutique et liste des articles |
| `photos/` | Photos d'origine des articles (`photos/exemples/` : photos Pexels des articles fictifs) |
| `src/style.css`, `src/commande.js` | Apparence et comportement (filtres, galerie, formulaire de commande) |
| `construire.py` | Fabrique le site dans `public/` : photos allégées en WebP, accueil, page d'aide, une page par article |
| `public/` | Le site prêt à mettre en ligne (refait à chaque construction, non suivi par git) |

## Construire et regarder le site

```bash
python3 construire.py
python3 -m http.server 8000 -d public
```

Puis ouvrir http://localhost:8000. Seule dépendance : Pillow (déjà installé).

## Ajouter un article

1. Mettre la photo dans `photos/`. Une chaussure détourée sur fond uni est recadrée automatiquement ;
   une photo portée est coupée au format 4:5.
2. Ajouter un bloc dans `produits` de `catalogue.json` :

```json
{
  "id": "robe-wax-bleue",
  "nom": "Robe wax bleue",
  "categorie": "pagne",
  "prix": 14000,
  "tailles": ["S", "M", "L", "XL"],
  "photos": ["robe-wax-bleue.jpg", "robe-wax-bleue-dos.jpg"],
  "cadrage": 0.4,
  "description": "Une ou deux phrases simples sur l'article."
}
```

- `id` : sert d'adresse de la page (`p/robe-wax-bleue.html`), en minuscules et sans accents.
- `categorie` : une des catégories de `categories` (robes, pagne, chaussures, sacs).
- `tailles` : des nombres pour les pointures (`[37, 38, 39]`), du texte pour les vêtements, `["Taille unique"]`, ou `[]` pour un sac.
- `cadrage` (photos portées seulement) : quelle hauteur garder en coupant, de 0 (le haut) à 1 (le bas).
- `zone` (facultatif) : `[gauche, haut, droite, bas]` en fractions, pour zoomer quand le mannequin est trop petit.
- L'ordre des articles dans le fichier est l'ordre d'affichage.

- Photo prise sur la table de la boutique : ajouter `"decor": true`. La photo reste entière (pas de
  recadrage) ; seule la lumière est rattrapée, sans toucher aux couleurs. Les cases du site sont carrées
  sur fond crème, la photo est posée au centre.
- Vidéo : la mettre dans `videos/` et ajouter `"video": "videos/nom.mp4"`. Sur la fiche, « Voir la vidéo »
  ne la télécharge qu'au toucher. Pour l'alléger : `ffmpeg -i entree.mp4 -an -vf "scale='min(720,iw)':-2"
  -c:v libx264 -crf 30 -movflags +faststart videos/nom.mp4`.
- `"type"` (ballerine, escarpin, slingback, mocassin, babies, mule, baskets) : tri sous l'onglet Chaussures.
- `"nouveau": true` : badge « Nouveau » sur la case.

3. Relancer `python3 construire.py`.

## Panier, retrait et ruptures

- La cliente ajoute plusieurs articles au panier (`panier.html`), choisit **retrait gratuit en point relais**
  ou **livraison à domicile** (`livraison` en francs), puis tout part dans un seul message WhatsApp.
- `boutique.retrait` : adresse du point relais. Vide = « adresse envoyée sur WhatsApp ».
- Rupture d'une taille : `"epuisees": ["XL"]` dans l'article. Article entier épuisé : `"epuise": true`.
- Sans panier possible (JavaScript coupé, Opera Mini, navigation privée stricte, script pas chargé) :
  la fiche reste un simple formulaire et le bouton devient « Commander sur WhatsApp ». Il envoie
  l'article et la taille choisie directement, sans passer par le panier.
- Guides des tailles et pointures : `guides` dans `catalogue.json` (mesures indicatives, à ajuster au vrai stock).

## Réglages de la boutique (`boutique` dans `catalogue.json`)

- `whatsapp` : le numéro qui reçoit les commandes, au format international sans `+` ni espaces
  (`2376XXXXXXXX`). **Vide pour l'instant** : la commande ouvre WhatsApp sans destinataire.
- `url` : l'adresse du site une fois en ligne. Elle sert aux aperçus de liens (la photo et le prix
  s'affichent quand on partage une page sur WhatsApp ou Facebook) et au plan du site.
- `livraison` : frais de livraison en francs, ajoutés au total.
- `exemples` : `true` affiche les articles fictifs marqués `"exemple": true`. **Passer à `false`
  avant la mise en ligne**, sinon des clientes pourraient commander des articles qui n'existent pas.

## À confirmer avant la mise en ligne

- Numéro WhatsApp Business de la boutique.
- Frais de livraison (1 000 F est une valeur de test) et villes desservies.
- Pointures de chaque modèle : 37 au 42 confirmé pour les modèles pointus, appliqué aux autres en attendant.
- Remplacer les articles d'exemple par le vrai stock.

## Crédits photo

Les photos de `photos/exemples/` viennent de [Pexels](https://www.pexels.com) (licence libre,
usage commercial autorisé, attribution non obligatoire). Identifiants dans les noms de fichiers.
Les photos de chaussures sont celles de la boutique.
