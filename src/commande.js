// Belle Allure : menu, recherche, filtres de l'accueil, galerie, panier et commande par WhatsApp.
// Aucune bibliothèque : le site doit rester léger pour les connexions lentes.
(function () {
  "use strict";

  var format = new Intl.NumberFormat("fr-FR");
  function prix(n) { return format.format(n) + " F"; }

  // Le navigateur peut refuser le stockage (navigation privée) : on s'en passe alors.
  function lire(cle) {
    try { return JSON.parse(localStorage.getItem(cle) || "null"); } catch (e) { return null; }
  }
  function ecrire(cle, valeur) {
    try { localStorage.setItem(cle, JSON.stringify(valeur)); } catch (e) { /* tant pis */ }
  }

  // Sans accents ni majuscules, pour que « creme » trouve « crème ».
  function simple(texte) {
    return texte.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
  }

  // ---------------------------------------------------------------- fenêtres (menu, volet de commande)
  function ouvrirFenetre(fenetre) {
    if (typeof fenetre.showModal === "function") fenetre.showModal();
    else fenetre.setAttribute("open", "");
    document.documentElement.classList.add("verrou");
  }
  function fermerFenetre(fenetre) {
    if (typeof fenetre.close === "function") fenetre.close();
    else fenetre.removeAttribute("open");
  }
  document.querySelectorAll("dialog").forEach(function (fenetre) {
    fenetre.addEventListener("close", function () { document.documentElement.classList.remove("verrou"); });
    // un toucher sur le fond grisé ferme la fenêtre
    fenetre.addEventListener("click", function (ev) { if (ev.target === fenetre) fermerFenetre(fenetre); });
    fenetre.querySelectorAll("[data-fermer]").forEach(function (b) {
      b.addEventListener("click", function () { fermerFenetre(fenetre); });
    });
  });

  // ---------------------------------------------------------------- en-tête
  function entete() {
    var haut = document.querySelector(".entete");
    if (haut && "ResizeObserver" in window) {
      new ResizeObserver(function () {
        document.documentElement.style.setProperty("--haut-entete", haut.offsetHeight + "px");
      }).observe(haut);
    }

    // boutons qui ouvrent une fenêtre : le menu, le guide des tailles…
    document.querySelectorAll("[data-ouvrir]").forEach(function (b) {
      b.addEventListener("click", function () { ouvrirFenetre(document.getElementById(b.getAttribute("data-ouvrir"))); });
    });
    var menu = document.getElementById("menu");
    // les liens du menu vers une catégorie de la page en cours : on ferme le menu
    menu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { fermerFenetre(menu); });
    });

    var loupe = document.querySelector("[data-basculer-recherche]");
    var recherche = document.querySelector("[data-recherche]");
    loupe.addEventListener("click", function () {
      var ouverte = recherche.classList.toggle("ouverte");
      loupe.setAttribute("aria-expanded", String(ouverte));
      if (ouverte) recherche.querySelector("input").focus();
    });
  }

  // ---------------------------------------------------------------- accueil : catégories, recherche
  function accueil() {
    var barre = document.querySelector("[data-filtres]");
    var grille = document.querySelector("[data-grille]");
    if (!barre || !grille) return;
    var boutons = Array.prototype.slice.call(barre.querySelectorAll("[data-filtre]"));
    var trait = barre.querySelector(".filtres-trait");
    var compte = document.querySelector("[data-compte]");
    var vide = document.querySelector("[data-vide]");
    var cartes = grille.querySelectorAll(".carte");
    var recherche = document.querySelector("[data-recherche]");
    var champ = recherche.querySelector("input");
    var etat = { categorie: "tout", texte: "" };

    function bouton(categorie) {
      return boutons.filter(function (b) { return b.getAttribute("data-filtre") === categorie; })[0];
    }

    function placerTrait() {
      var b = bouton(etat.categorie);
      trait.style.width = b.offsetWidth + "px";
      trait.style.transform = "translateX(" + b.offsetLeft + "px)";
      barre.scrollTo({ left: b.offsetLeft - (barre.clientWidth - b.offsetWidth) / 2, behavior: "smooth" });
    }

    function appliquer() {
      var mots = simple(etat.texte);
      var n = 0;
      boutons.forEach(function (b) {
        b.setAttribute("aria-pressed", String(b.getAttribute("data-filtre") === etat.categorie));
      });
      cartes.forEach(function (c) {
        var garde = (etat.categorie === "tout" || c.getAttribute("data-categorie") === etat.categorie) &&
          (!mots || simple(c.getAttribute("data-nom")).indexOf(mots) !== -1);
        c.hidden = !garde;
        c.classList.remove("apparait");
        if (garde) {
          n++;
          void c.offsetWidth; // relance l'animation d'apparition
          c.classList.add("apparait");
        }
      });
      compte.textContent = n;
      vide.hidden = n > 0;
      placerTrait();
    }

    // revient en haut de la grille, juste sous les onglets
    function allerAuxArticles(doux) {
      var haut = grille.getBoundingClientRect().top + window.scrollY - barre.offsetHeight -
        parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--haut-entete")) - 8;
      if (Math.abs(window.scrollY - haut) > 4) window.scrollTo({ top: haut, behavior: doux ? "smooth" : "auto" });
    }

    function choisir(categorie, doux) {
      etat.categorie = bouton(categorie) ? categorie : "tout";
      appliquer();
      allerAuxArticles(doux);
    }

    boutons.forEach(function (b) {
      b.addEventListener("click", function () {
        history.replaceState(null, "", "#" + b.getAttribute("data-filtre"));
        choisir(b.getAttribute("data-filtre"), true);
      });
    });
    document.querySelector("[data-filtre-tout]").addEventListener("click", function () {
      etat.texte = "";
      champ.value = "";
      choisir("tout", true);
    });

    // liens « #robes », « #chaussures »… : catégories rondes, menu, bas de page
    function depuisAdresse(doux) {
      var cle = decodeURIComponent(location.hash.slice(1));
      if (cle === "articles" || bouton(cle)) choisir(cle === "articles" ? "tout" : cle, doux);
    }
    window.addEventListener("hashchange", function () { depuisAdresse(true); });

    // recherche : la grille se filtre pendant la frappe
    champ.addEventListener("input", function () {
      etat.texte = champ.value;
      appliquer();
    });
    recherche.addEventListener("submit", function (ev) {
      ev.preventDefault();
      champ.blur();
      allerAuxArticles(true);
    });

    var q = new URLSearchParams(location.search).get("q");
    if (q) {
      etat.texte = champ.value = q;
      recherche.classList.add("ouverte");
      document.querySelector("[data-basculer-recherche]").setAttribute("aria-expanded", "true");
    }
    barre.classList.add("filtres-pret");
    appliquer();
    if (location.hash) depuisAdresse(false);
    else if (q) allerAuxArticles(false);
    window.addEventListener("resize", placerTrait);
  }

  // ---------------------------------------------------------------- galerie de la fiche
  function galerie() {
    var piste = document.querySelector("[data-piste]");
    var points = document.querySelectorAll("[data-point]");
    if (!piste || !points.length) return;
    var photos = piste.querySelectorAll("img");

    points.forEach(function (p) {
      p.addEventListener("click", function () {
        piste.scrollTo({ left: photos[Number(p.getAttribute("data-point"))].offsetLeft, behavior: "smooth" });
      });
    });

    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (en) {
        if (!en.isIntersecting) return;
        var i = Array.prototype.indexOf.call(photos, en.target);
        points.forEach(function (p, j) {
          if (i === j) p.setAttribute("aria-current", "true");
          else p.removeAttribute("aria-current");
        });
      });
    }, { root: piste, threshold: 0.6 });
    photos.forEach(function (img) { observateur.observe(img); });
  }

  // ---------------------------------------------------------------- photos en plein écran
  function visionneuse() {
    var fenetre = document.getElementById("visionneuse");
    if (!fenetre) return;
    var piste = fenetre.querySelector("[data-visionneuse-piste]");
    var compte = fenetre.querySelector("[data-visionneuse-compte]");
    var nb = piste.querySelectorAll("img").length;

    document.querySelectorAll("[data-agrandir]").forEach(function (b) {
      b.addEventListener("click", function () {
        ouvrirFenetre(fenetre);
        piste.scrollLeft = Number(b.getAttribute("data-agrandir")) * piste.clientWidth;
      });
    });
    if (compte) {
      piste.addEventListener("scroll", function () {
        compte.textContent = (Math.round(piste.scrollLeft / piste.clientWidth) + 1) + " / " + nb;
      }, { passive: true });
    }
  }

  // ---------------------------------------------------------------- panier (gardé sur le téléphone)
  var CLE_PANIER = "belle-allure-panier";
  function lirePanier() { return lire(CLE_PANIER) || []; }
  function ecrirePanier(lignes) { ecrire(CLE_PANIER, lignes); majPastille(); }
  function nombreArticles(lignes) { return lignes.reduce(function (n, l) { return n + l.quantite; }, 0); }

  // la pastille sur l'icône du panier, dans l'en-tête de toutes les pages
  function majPastille() {
    var n = nombreArticles(lirePanier());
    document.querySelectorAll("[data-pastille]").forEach(function (p) {
      p.textContent = n > 9 ? "9+" : n;
      p.hidden = n === 0;
    });
    document.querySelectorAll("[data-lien-panier]").forEach(function (a) {
      a.setAttribute("aria-label", n ? "Panier, " + n + (n > 1 ? " articles" : " article") : "Panier, vide");
    });
  }

  // ---------------------------------------------------------------- fiche : ajouter au panier
  function ajouter() {
    var fiche = document.querySelector("[data-produit]");
    var boutons = document.querySelectorAll("[data-ajouter]");
    if (!fiche || !boutons.length) return;
    var id = fiche.getAttribute("data-produit");
    var libelle = fiche.getAttribute("data-taille-libelle") || "Taille";
    var tailles = document.querySelector("[data-tailles]");
    var erreurTaille = document.querySelector("[data-erreur-taille]");
    var choisie = document.querySelector("[data-taille-choisie]");
    var confirmation = document.getElementById("ajoute");

    function tailleChoisie() {
      var t = tailles && tailles.querySelector('input[name="taille"]:checked');
      return t ? t.value : "";
    }

    if (tailles) {
      tailles.addEventListener("change", function () {
        choisie.textContent = tailleChoisie();
        tailles.classList.remove("invalide");
        erreurTaille.hidden = true;
      });
    }

    boutons.forEach(function (b) {
      b.addEventListener("click", function () {
        // comme sur les grands sites, la taille doit être choisie avant
        if (tailles && !tailleChoisie()) {
          erreurTaille.hidden = false;
          tailles.classList.add("invalide");
          tailles.classList.remove("secoue");
          void tailles.offsetWidth;
          tailles.classList.add("secoue");
          tailles.scrollIntoView({ block: "center", behavior: "smooth" });
          return;
        }
        var taille = tailleChoisie();
        var lignes = lirePanier();
        var deja = lignes.filter(function (l) { return l.id === id && l.taille === taille; })[0];
        if (deja) deja.quantite = Math.min(10, deja.quantite + 1);
        else lignes.push({ id: id, taille: taille, quantite: 1 });
        ecrirePanier(lignes);

        var unique = tailles && tailles.querySelectorAll('input[name="taille"]').length === 1;
        confirmation.querySelector("[data-detail]").textContent =
          !taille ? "" : unique ? taille : libelle + " : " + taille;
        ouvrirFenetre(confirmation);
      });
    });

    // Barre « Ajouter au panier » en bas de l'écran (téléphone), tant que le bouton principal n'est pas à l'écran.
    var barre = document.querySelector("[data-barre]");
    var principal = document.querySelector(".bouton-ajouter");
    if (barre && principal && "IntersectionObserver" in window) {
      new IntersectionObserver(function (e) {
        barre.classList.toggle("visible", !e[0].isIntersecting);
      }).observe(principal);
    }
  }

  // ---------------------------------------------------------------- page panier : la commande
  function chiffres(telephone) {
    var c = telephone.replace(/\D/g, "");
    if (c.indexOf("00237") === 0) c = c.slice(5);
    else if (c.indexOf("237") === 0 && c.length === 12) c = c.slice(3);
    return c;
  }

  function lisible(numero) {
    return numero.replace(/^(\d{3})(\d{2})(\d{2})(\d{2})$/, "$1 $2 $3 $4"); // 6XX XX XX XX
  }

  function echapper(texte) {
    return String(texte).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // Une règle par champ : le message affiché sous le champ, ou "" si tout va bien.
  var REGLES = {
    nom: function (v) { return v.trim().length >= 2 ? "" : "Indiquez votre nom."; },
    telephone: function (v) {
      var n = chiffres(v);
      if (!n) return "Indiquez votre numéro.";
      if (n.length !== 9) return "Le numéro doit avoir 9 chiffres, par exemple 6XX XX XX XX.";
      if (!/^[26]/.test(n)) return "Le numéro doit commencer par 6, ou par 2 pour un fixe.";
      return "";
    },
    lieu: function (v) { return v.trim().length >= 3 ? "" : "Indiquez la ville, le quartier et un repère."; }
  };

  function panier() {
    var form = document.querySelector("[data-panier-formulaire]");
    if (!form) return;
    var catalogue = JSON.parse(document.getElementById("catalogue").textContent);
    var liste = form.querySelector("[data-panier-liste]");
    var vide = document.querySelector("[data-panier-vide]");
    var merci = document.querySelector("[data-merci]");
    var champLieu = form.querySelector("[data-champ-lieu]");
    var d = form.dataset;
    var livraison = Number(d.livraison);
    var essaye = false;

    function remise() { return form.querySelector('input[name="remise"]:checked').value; }
    function champsActifs() { return remise() === "livraison" ? ["nom", "telephone", "lieu"] : ["nom", "telephone"]; }

    // Les articles retirés du catalogue disparaissent ; une taille épuisée entre-temps est signalée.
    function lignesValides() {
      return lirePanier().filter(function (l) { return catalogue[l.id]; });
    }
    function indisponible(l) {
      var a = catalogue[l.id];
      return a.epuise || a.epuisees.indexOf(l.taille) !== -1;
    }

    function afficher() {
      var lignes = lignesValides();
      vide.hidden = lignes.length > 0;
      form.hidden = lignes.length === 0;
      liste.innerHTML = lignes.map(function (l, i) {
        var a = catalogue[l.id];
        var detail = !l.taille ? "" : a.tailles.length === 1 ? l.taille : a.libelle + " : " + l.taille;
        return '<li class="ligne">' +
          '<a class="ligne-photo" href="' + a.lien + '"><img src="' + a.image + '" width="400" height="500" alt=""></a>' +
          '<div class="ligne-infos">' +
            '<a class="ligne-nom" href="' + a.lien + '">' + echapper(a.nom) + "</a>" +
            (detail ? '<p class="ligne-detail">' + echapper(detail) + "</p>" : "") +
            '<p class="ligne-prix">' + prix(a.prix * l.quantite) +
              (l.quantite > 1 ? ' <span class="ligne-unite">(' + l.quantite + " × " + prix(a.prix) + ")</span>" : "") + "</p>" +
            (indisponible(l) ? '<p class="ligne-alerte">Épuisé entre-temps : retirez-le pour commander.</p>' : "") +
            '<div class="ligne-actions">' +
              '<div class="quantite-boutons" role="group" aria-label="Quantité de ' + echapper(a.nom) + '">' +
                '<button type="button" data-moins="' + i + '" aria-label="Une de moins"' + (l.quantite <= 1 ? " disabled" : "") + ">−</button>" +
                "<output>" + l.quantite + "</output>" +
                '<button type="button" data-plus="' + i + '" aria-label="Une de plus"' + (l.quantite >= 10 ? " disabled" : "") + ">+</button>" +
              "</div>" +
              '<button type="button" class="ligne-retirer" data-retirer="' + i + '">Retirer</button>' +
            "</div>" +
          "</div></li>";
      }).join("");
      recalculer();
    }

    function sousTotal() {
      return lignesValides().reduce(function (t, l) { return t + catalogue[l.id].prix * l.quantite; }, 0);
    }
    function frais() { return remise() === "livraison" ? livraison : 0; }

    function recalculer() {
      var n = nombreArticles(lignesValides());
      form.querySelector("[data-recap-detail]").textContent =
        n + (n > 1 ? " articles" : " article") + (frais() ? " + livraison " + prix(frais()) : ", retrait gratuit");
      form.querySelector("[data-recap-total]").textContent = prix(sousTotal() + frais());
    }

    liste.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b) return;
      var lignes = lignesValides();
      if (b.hasAttribute("data-plus")) lignes[Number(b.getAttribute("data-plus"))].quantite++;
      else if (b.hasAttribute("data-moins")) lignes[Number(b.getAttribute("data-moins"))].quantite--;
      else if (b.hasAttribute("data-retirer")) lignes.splice(Number(b.getAttribute("data-retirer")), 1);
      else return;
      ecrirePanier(lignes);
      afficher();
    });

    form.addEventListener("change", function (ev) {
      if (ev.target.name !== "remise") return;
      champLieu.hidden = remise() !== "livraison";
      if (champLieu.hidden) {
        form.elements.lieu.removeAttribute("aria-invalid");
        document.getElementById("e-lieu").hidden = true;
      }
      recalculer();
    });

    // On retrouve les coordonnées de la cliente si elle a déjà commandé sur ce téléphone.
    var client = lire("belle-allure-client");
    if (client) {
      ["nom", "telephone", "lieu"].forEach(function (nom) {
        if (client[nom] && !form.elements[nom].value) form.elements[nom].value = client[nom];
      });
    }

    // Erreur affichée sous le champ concerné ; elle disparaît dès que c'est corrigé.
    function verifier(nom) {
      var champ = form.elements[nom];
      var message = REGLES[nom](champ.value);
      var zone = document.getElementById(champ.getAttribute("aria-describedby").split(" ").pop());
      zone.textContent = message;
      zone.hidden = !message;
      if (message) champ.setAttribute("aria-invalid", "true");
      else champ.removeAttribute("aria-invalid");
      return !message;
    }

    ["nom", "telephone", "lieu"].forEach(function (nom) {
      var champ = form.elements[nom];
      champ.addEventListener("blur", function () {
        if (champsActifs().indexOf(nom) === -1) return;
        if (champ.value.trim() || essaye) verifier(nom);
        if (nom === "telephone" && !REGLES.telephone(champ.value)) champ.value = lisible(chiffres(champ.value));
      });
      champ.addEventListener("input", function () {
        if (champ.getAttribute("aria-invalid") === "true") verifier(nom);
      });
      // touche « Suivant » du clavier : champ suivant ; « Envoyer » sur le dernier
      champ.addEventListener("keydown", function (ev) {
        var ordre = champsActifs();
        var i = ordre.indexOf(nom);
        if (ev.key === "Enter" && i !== -1 && i < ordre.length - 1) {
          ev.preventDefault();
          form.elements[ordre[i + 1]].focus();
        }
      });
    });
    form.elements.telephone.setAttribute("enterkeyhint", "next");

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      essaye = true;
      var lignes = lignesValides();
      if (lignes.some(indisponible)) {
        liste.querySelector(".ligne-alerte").scrollIntoView({ block: "center" });
        return;
      }
      var faux = champsActifs().filter(function (nom) { return !verifier(nom); });
      if (faux.length) {
        var champ = form.elements[faux[0]];
        champ.focus();
        champ.scrollIntoView({ block: "center" });
        return;
      }

      var champs = form.elements;
      var numero = chiffres(champs.telephone.value);
      var livrer = remise() === "livraison";
      var texte = ["Bonjour Belle Allure, je voudrais commander :", ""];
      lignes.forEach(function (l, i) {
        var a = catalogue[l.id];
        var detail = !l.taille ? "" : a.tailles.length === 1 ? ", " + l.taille.toLowerCase() : ", " + a.libelle.toLowerCase() + " " + l.taille;
        texte.push((i + 1) + ". *" + a.nom + "*" + detail + " : " + l.quantite + " × " + prix(a.prix));
        if (d.url) texte.push("   " + d.url + "/" + a.lien);
      });
      texte.push(
        "",
        livrer ? "Livraison à domicile : " + prix(livraison) : "Retrait en point relais (gratuit)",
        "Total : *" + prix(sousTotal() + frais()) + "*",
        "",
        "Nom : " + champs.nom.value.trim(),
        "Téléphone : " + lisible(numero)
      );
      if (livrer) texte.push("Lieu de livraison : " + champs.lieu.value.trim());
      texte.push("", livrer ? "Je paie à la livraison." : "Je paie au retrait.");

      ecrire("belle-allure-client", {
        nom: champs.nom.value.trim(), telephone: lisible(numero), lieu: champs.lieu.value.trim()
      });

      // Quand la cliente revient de WhatsApp, on lui rappelle de toucher « Envoyer » là-bas.
      var adresse = "https://wa.me/" + (d.whatsapp || "") + "?text=" + encodeURIComponent(texte.join("\n"));
      merci.querySelector("[data-relancer]").href = adresse;
      form.hidden = true;
      merci.hidden = false;
      window.scrollTo(0, 0);
      window.location.href = adresse;
    });

    merci.querySelector("[data-terminer]").addEventListener("click", function () {
      ecrirePanier([]);
      window.location.href = "./";
    });

    // le panier a pu changer dans un autre onglet
    window.addEventListener("storage", function (ev) { if (ev.key === CLE_PANIER && merci.hidden) afficher(); });
    afficher();
  }

  entete();
  majPastille();
  accueil();
  galerie();
  visionneuse();
  ajouter();
  panier();
  // retour par le bouton « Précédent » : la pastille doit refléter le panier actuel
  window.addEventListener("pageshow", majPastille);
})();
