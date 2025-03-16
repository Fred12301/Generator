import os
import subprocess
from threading import Thread
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

class MainInterface(BoxLayout):
    def __init__(self, **kwargs):
        super(MainInterface, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 10
        self.spacing = 10

        # Zone de log dans une ScrollView pour le défilement
        self.log_text = TextInput(readonly=True, multiline=True, size_hint_y=None)
        self.log_text.bind(minimum_height=self.log_text.setter('height'))
        self.log_text.height = 300
        self.log_scroll = ScrollView(size_hint_y=0.4)
        self.log_scroll.add_widget(self.log_text)
        self.add_widget(self.log_scroll)

        # Zone de configuration : manufacturer, codename et dossier de sortie
        config_layout = BoxLayout(orientation="vertical", size_hint_y=0.3, spacing=10)
        self.manufacturer_input = TextInput(hint_text="Nom du manufacturer", multiline=False)
        self.codename_input = TextInput(hint_text="Codename", multiline=False)
        self.output_dir_label = TextInput(text="Dossier de sortie non choisi", readonly=True, multiline=False)
        btn_choose_output = Button(text="Choisir dossier de sortie")
        btn_choose_output.bind(on_press=self.open_directory_chooser)
        config_layout.add_widget(self.manufacturer_input)
        config_layout.add_widget(self.codename_input)
        config_layout.add_widget(self.output_dir_label)
        config_layout.add_widget(btn_choose_output)
        self.add_widget(config_layout)

        # Zone des boutons d'installation et de génération
        button_layout = BoxLayout(size_hint_y=0.2, spacing=10)
        btn_install = Button(text="Installer twrpdtgen et cpio")
        btn_install.bind(on_press=self.install_tools)
        btn_generate = Button(text="Générer votre arborecenses")
        btn_generate.bind(on_press=self.open_filechooser)
        button_layout.add_widget(btn_install)
        button_layout.add_widget(btn_generate)
        self.add_widget(button_layout)

        # Stockage du dossier de sortie choisi
        self.output_dir = None

    def log_message(self, message):
        """Ajoute un message dans le log et force le scroll vers le bas."""
        self.log_text.text += message + "\n"
        Clock.schedule_once(lambda dt: self.log_scroll.scroll_to(self.log_text), 0)

    def run_command_thread(self, cmd, callback):
        """Exécute une commande en arrière-plan et transmet la sortie via callback."""
        def target():
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = proc.stdout + proc.stderr
            Clock.schedule_once(lambda dt: callback(output), 0)
        Thread(target=target, daemon=True).start()

    def install_tools(self, instance):
        self.log_message("Installation de twrpdtgen et cpio en cours...")
        # Installation de twrpdtgen via pip
        pip_cmd = ["pip3", "install", "twrpdtgen"]
        self.log_message("Exécution de : " + " ".join(pip_cmd))
        self.run_command_thread(pip_cmd, lambda output: self.log_message("twrpdtgen: " + output))

        # Installation de cpio en fonction du système et du gestionnaire de paquets
        if os.name == "posix":
            # Priorité : dnf / apt / pacman
            if os.path.exists("/usr/bin/dnf"):
                pkg_cmd = ["sudo", "dnf", "install", "-y", "cpio"]
            elif os.path.exists("/usr/bin/apt"):
                pkg_cmd = ["sudo", "apt", "install", "-y", "cpio"]
            elif os.path.exists("/usr/bin/pacman"):
                pkg_cmd = ["sudo", "pacman", "-S", "--noconfirm", "cpio"]
            else:
                self.log_message("Gestionnaire de paquets non supporté pour cpio.")
                return
            self.log_message("Exécution de : " + " ".join(pkg_cmd))
            self.run_command_thread(pkg_cmd, lambda output: self.log_message("cpio: " + output))
        elif os.name == "nt":
            # Sous Windows, tenter d'installer cpio via pip (s'il existe)
            pip_cmd_win = ["pip", "install", "cpio"]
            self.log_message("Exécution de : " + " ".join(pip_cmd_win))
            self.run_command_thread(pip_cmd_win, lambda output: self.log_message("cpio: " + output))
        else:
            self.log_message("Installation de cpio non supportée sur ce système.")

    def open_directory_chooser(self, instance):
        """Ouvre une fenêtre pour choisir le dossier de sortie."""
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        filechooser = FileChooserListView(dirselect=True, size_hint_y=0.8)
        layout.add_widget(filechooser)
        button_layout = BoxLayout(size_hint_y=0.2, spacing=10)
        btn_select = Button(text="Sélectionner")
        btn_cancel = Button(text="Annuler")
        button_layout.add_widget(btn_select)
        button_layout.add_widget(btn_cancel)
        layout.add_widget(button_layout)
        popup = Popup(title="Choisissez un dossier", content=layout, size_hint=(0.9, 0.9))
        btn_select.bind(on_press=lambda x: self.directory_chosen(filechooser.path, popup))
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def directory_chosen(self, path, popup):
        self.output_dir = path
        self.output_dir_label.text = "Dossier de sortie: " + path
        self.log_message("Dossier de sortie choisi: " + path)
        popup.dismiss()

    def open_filechooser(self, instance):
        """Ouvre une fenêtre pour sélectionner un fichier .img."""
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        filechooser = FileChooserListView(filters=["*.img"], size_hint_y=0.8)
        layout.add_widget(filechooser)
        button_layout = BoxLayout(size_hint_y=0.2, spacing=10)
        btn_select = Button(text="Sélectionner")
        btn_cancel = Button(text="Annuler")
        button_layout.add_widget(btn_select)
        button_layout.add_widget(btn_cancel)
        layout.add_widget(button_layout)
        popup = Popup(title="Choisissez un fichier .img", content=layout, size_hint=(0.9, 0.9))
        btn_select.bind(on_press=lambda x: self.file_chosen(filechooser.selection, popup))
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def file_chosen(self, selection, popup):
        if selection:
            image_path = selection[0]
            self.log_message("Fichier image choisi: " + image_path)
            popup.dismiss()
            self.generate_device_tree(image_path)
        else:
            self.log_message("Aucun fichier sélectionné.")

    def generate_device_tree(self, image_path):
        """Génère l'arborecenses en utilisant le module twrpdtgen avec les paramètres choisis."""
        manufacturer = self.manufacturer_input.text.strip()
        codename = self.codename_input.text.strip()
        if not manufacturer or not codename:
            self.log_message("Veuillez saisir le manufacturer et le codename.")
            return

        # Construction du dossier de sortie : dossier choisi ou chemin par défaut
        if self.output_dir:
            output_path = os.path.join(self.output_dir, manufacturer, codename)
        else:
            output_path = os.path.join("output", manufacturer, codename)

        self.log_message("Génération de l'arborecenses depuis l'image: " + image_path)
        self.log_message("Dossier de sortie: " + output_path)

        def target():
            try:
                from twrpdtgen.device_tree import DeviceTree
                image_path_obj = Path(image_path)
                output_path_obj = Path(output_path)
                device_tree = DeviceTree(image_path_obj)
                device_tree.dump_to_folder(output_path_obj)
                result = "Arborecenses généré avec succès dans: " + str(output_path_obj)
            except Exception as e:
                result = "Erreur lors de la génération: " + str(e)
            Clock.schedule_once(lambda dt: self.log_message(result), 0)
        Thread(target=target, daemon=True).start()

class MainApp(App):
    def build(self):
        return MainInterface()

if __name__ == "__main__":
    MainApp().run()