"""
NeonVIEW - Navigateur français (version Android)

Version Kivy + WebView Android natif (android.webkit.WebView via pyjnius).
Même interface que la version PyQt5 : barre d'adresse, onglets, retour/avancer,
actualiser, accueil, nouvel onglet, traduction en français.
"""
from urllib.parse import quote, urlparse

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex, platform

ACCUEIL = "https://www.google.com/?hl=fr"
LANGUE = "fr-FR,fr;q=0.9,en;q=0.8"

# Couleurs (reprises de la version PyQt5)
FOND = get_color_from_hex("#0b1020")
CHAMP = get_color_from_hex("#1b2540")
VIOLET = get_color_from_hex("#7565ed")
ONGLET = get_color_from_hex("#202944")

H_ADRESSE = dp(48)
H_BOUTONS = dp(44)
H_ONGLETS = dp(40)
H_BARRE = H_ADRESSE + H_BOUTONS + H_ONGLETS + dp(12)

ANDROID = platform == "android"

if ANDROID:
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    WebView = autoclass("android.webkit.WebView")
    WebViewClient = autoclass("android.webkit.WebViewClient")
    WebChromeClient = autoclass("android.webkit.WebChromeClient")
    LayoutParams = autoclass("android.widget.FrameLayout$LayoutParams")
    HashMap = autoclass("java.util.HashMap")
    View = autoclass("android.view.View")
else:
    def run_on_ui_thread(f):
        return f


def construire_url(texte):
    """Même logique que la version PyQt5 : adresse ou recherche Google FR."""
    texte = texte.strip()
    if not texte:
        return None

    if " " in texte:
        return "https://www.google.com/search?hl=fr&q=" + quote(texte)

    adresse = texte
    if not adresse.startswith(("https://", "http://")):
        adresse = "https://" + adresse

    analyse = urlparse(adresse)
    if not analyse.hostname or "." not in analyse.hostname:
        return "https://www.google.com/search?hl=fr&q=" + quote(texte)
    return adresse


class Onglet:
    """Un onglet = un android.webkit.WebView natif."""

    def __init__(self):
        self.webview = None
        self.url = ""
        self.titre = "Nouvel onglet"
        self.peut_reculer = False
        self.peut_avancer = False

    # ---- à exécuter dans le thread UI Android ----
    def _charger(self, url):
        if self.webview is None:
            return
        entetes = HashMap()
        entetes.put("Accept-Language", LANGUE)
        self.webview.loadUrl(url, entetes)

    @run_on_ui_thread
    def creer(self, haut, hauteur, url):
        activity = PythonActivity.mActivity
        wv = WebView(activity)
        reglages = wv.getSettings()
        reglages.setJavaScriptEnabled(True)
        reglages.setDomStorageEnabled(True)
        reglages.setBuiltInZoomControls(True)
        reglages.setDisplayZoomControls(False)
        reglages.setUseWideViewPort(True)
        reglages.setLoadWithOverviewMode(True)
        # Garde la navigation dans l'application
        wv.setWebViewClient(WebViewClient())
        wv.setWebChromeClient(WebChromeClient())

        params = LayoutParams(-1, hauteur)
        params.topMargin = haut
        activity.addContentView(wv, params)
        self.webview = wv
        self._charger(url)

    @run_on_ui_thread
    def placer(self, haut, hauteur):
        if self.webview is None:
            return
        params = LayoutParams(-1, hauteur)
        params.topMargin = haut
        self.webview.setLayoutParams(params)

    @run_on_ui_thread
    def afficher(self, visible):
        if self.webview is not None:
            self.webview.setVisibility(View.VISIBLE if visible else View.GONE)

    @run_on_ui_thread
    def aller(self, url):
        self._charger(url)

    @run_on_ui_thread
    def reculer(self):
        if self.webview is not None and self.webview.canGoBack():
            self.webview.goBack()

    @run_on_ui_thread
    def avancer(self):
        if self.webview is not None and self.webview.canGoForward():
            self.webview.goForward()

    @run_on_ui_thread
    def actualiser(self):
        if self.webview is not None:
            self.webview.reload()

    @run_on_ui_thread
    def synchroniser(self):
        wv = self.webview
        if wv is None:
            return
        self.url = wv.getUrl() or self.url
        self.titre = wv.getTitle() or self.titre
        self.peut_reculer = bool(wv.canGoBack())
        self.peut_avancer = bool(wv.canGoForward())

    @run_on_ui_thread
    def detruire(self):
        wv = self.webview
        if wv is None:
            return
        wv.setVisibility(View.GONE)
        parent = wv.getParent()
        if parent is not None:
            parent.removeView(wv)
        wv.destroy()
        self.webview = None


def bouton(texte, action, largeur=None):
    b = Button(
        text=texte,
        background_normal="",
        background_color=VIOLET,
        color=(1, 1, 1, 1),
        font_size=dp(13),
    )
    if largeur:
        b.size_hint_x = None
        b.width = largeur
    b.bind(on_release=lambda *_: action())
    return b


class NeonVIEW(App):
    title = "NeonVIEW - Navigateur français"

    def build(self):
        Window.clearcolor = FOND
        self.onglets = []
        self.actif = -1
        self._titres_affiches = None

        racine = BoxLayout(orientation="vertical", padding=dp(4), spacing=dp(4))

        # Barre d'adresse
        self.adresse = TextInput(
            hint_text="Rechercher ou saisir une adresse...",
            multiline=False,
            size_hint_y=None,
            height=H_ADRESSE,
            background_normal="",
            background_active="",
            background_color=CHAMP,
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(1, 1, 1, 0.5),
            cursor_color=(1, 1, 1, 1),
            padding=[dp(12), dp(12), dp(12), dp(8)],
            input_type="url",
            write_tab=False,
        )
        self.adresse.bind(on_text_validate=lambda *_: self.ouvrir())
        racine.add_widget(self.adresse)

        # Boutons
        rangee = BoxLayout(size_hint_y=None, height=H_BOUTONS, spacing=dp(4))
        for texte, action in [
            ("←", self.retour),
            ("→", self.avancer),
            ("↻", self.actualiser),
            ("Accueil", self.accueil),
            ("+", self.nouvel_onglet),
            ("FR", self.traduire),
            ("✕", self.fermer_onglet_actif),
        ]:
            rangee.add_widget(bouton(texte, action))
        racine.add_widget(rangee)

        # Barre d'onglets
        self.defilement = ScrollView(
            size_hint_y=None, height=H_ONGLETS, do_scroll_y=False
        )
        self.barre_onglets = BoxLayout(
            size_hint_x=None, spacing=dp(2), height=H_ONGLETS
        )
        self.barre_onglets.bind(minimum_width=self.barre_onglets.setter("width"))
        self.defilement.add_widget(self.barre_onglets)
        racine.add_widget(self.defilement)

        # Zone réservée au WebView natif (dessiné par Android au-dessus)
        racine.add_widget(Label(text="" if ANDROID else
                                "NeonVIEW fonctionne uniquement sur Android."))

        Window.bind(on_keyboard=self.touche, on_resize=self.redimensionner)
        Clock.schedule_once(lambda *_: self.nouvel_onglet(), 0.3)
        Clock.schedule_interval(self.synchroniser, 0.4)
        return racine

    # ---------- géométrie ----------
    def haut_webview(self):
        return int(H_BARRE + dp(8))

    def hauteur_webview(self):
        return max(int(Window.height - self.haut_webview()), 100)

    def redimensionner(self, *_):
        for o in self.onglets:
            o.placer(self.haut_webview(), self.hauteur_webview())

    # ---------- onglets ----------
    def onglet_actuel(self):
        if 0 <= self.actif < len(self.onglets):
            return self.onglets[self.actif]
        return None

    def nouvel_onglet(self):
        if not ANDROID:
            return
        o = Onglet()
        self.onglets.append(o)
        o.creer(self.haut_webview(), self.hauteur_webview(), ACCUEIL)
        self.choisir(len(self.onglets) - 1)

    def choisir(self, index):
        self.actif = index
        for i, o in enumerate(self.onglets):
            o.afficher(i == index)
        self._titres_affiches = None
        self.maj_interface(force=True)

    def fermer_onglet(self, index):
        if not (0 <= index < len(self.onglets)):
            return
        if len(self.onglets) == 1:
            self.onglets[0].aller(ACCUEIL)
            return
        self.onglets[index].detruire()
        del self.onglets[index]
        self.choisir(min(index, len(self.onglets) - 1))

    def fermer_onglet_actif(self):
        self.fermer_onglet(self.actif)

    # ---------- actions ----------
    def ouvrir(self):
        url = construire_url(self.adresse.text)
        o = self.onglet_actuel()
        if url and o:
            o.aller(url)
            self.adresse.focus = False

    def retour(self):
        o = self.onglet_actuel()
        if o:
            o.reculer()

    def avancer(self):
        o = self.onglet_actuel()
        if o:
            o.avancer()

    def actualiser(self):
        o = self.onglet_actuel()
        if o:
            o.actualiser()

    def accueil(self):
        o = self.onglet_actuel()
        if o:
            o.aller(ACCUEIL)

    def traduire(self):
        o = self.onglet_actuel()
        if not o or not o.url.startswith(("http://", "https://")):
            return
        o.aller(
            "https://translate.google.com/translate?sl=auto&tl=fr&u="
            + quote(o.url, safe="")
        )

    def touche(self, window, key, *args):
        # Bouton « retour » d'Android
        if key == 27:
            o = self.onglet_actuel()
            if o and o.peut_reculer:
                o.reculer()
                return True
            if len(self.onglets) > 1:
                self.fermer_onglet(self.actif)
                return True
        return False

    # ---------- synchronisation interface ----------
    def synchroniser(self, dt):
        for o in self.onglets:
            o.synchroniser()
        self.maj_interface()

    def maj_interface(self, force=False):
        o = self.onglet_actuel()
        if o and not self.adresse.focus and (force or self.adresse.text != o.url):
            self.adresse.text = o.url

        titres = tuple((x.titre or "Nouvel onglet")[:18] for x in self.onglets) + (
            self.actif,
        )
        if titres == self._titres_affiches:
            return
        self._titres_affiches = titres

        self.barre_onglets.clear_widgets()
        for i, o2 in enumerate(self.onglets):
            b = Button(
                text=titres[i],
                size_hint_x=None,
                width=dp(130),
                background_normal="",
                background_color=VIOLET if i == self.actif else ONGLET,
                color=(1, 1, 1, 1),
                font_size=dp(12),
            )
            b.bind(on_release=lambda _b, idx=i: self.choisir(idx))
            self.barre_onglets.add_widget(b)

    def on_pause(self):
        return True

    def on_resume(self):
        self.redimensionner()


if __name__ == "__main__":
    NeonVIEW().run()
