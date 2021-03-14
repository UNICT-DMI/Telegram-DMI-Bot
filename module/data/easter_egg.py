# -*- coding: utf-8 -*-
"""EasterEgg class"""
from random import choice


class EasterEgg():
    """You got gnomed"""

    @staticmethod
    def get_santino() -> str:
        elements = [
            "@Santinol",
            "https://s18.postimg.org/t13s9lai1/photo_2016_11_24_11_04_42.jpg",
            "https://s11.postimg.org/yiwugh4ib/photo_2016_11_24_11_04_31.jpg",
            "https://s12.postimg.org/5d7y88pj1/photo_2016_11_24_11_04_29.jpg",
        ]

        return choice(elements)

    @staticmethod
    def get_smonta_portoni() -> str:
        elements = [
            "$ sudo umount portoni",
            "@TkdAlex",
            "https://s16.postimg.org/5a6khjb5h/smonta_portoni.jpg",
            "https://s16.postimg.org/rz8117y9x/idraulico.jpg",
        ]
        return choice(elements)

    @staticmethod
    def get_bladrim() -> str:
        elements = ["Per maggiori informazioni contatta @bladrim"]
        return choice(elements)

    @staticmethod
    def get_lei_che_ne_pensa_signorina() -> str:
        elements = [
            "🎤 Pronto? Si sente?",
            "Cosa ne pensa lei signorina?",
            "Tranquilli che l'anno prossimo prendo la pensione e me ne vado a Cuba 🇨🇺",
            "Che faccio me ne vado? Va bene me ne vado 🚪",
            "Che ore sono? ⌚ ... Appena dite voi me ne vado",
            "Vieni tu a spiegare, così io mi riposo!",
        ]
        return choice(elements)
