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
    @staticmethod
    def get_uni_bandita() -> str:
        elements = [
            "[Te lo prometto!](https://t.me/assolvo_ad_una_promessa/2)",
            "[Siamo su RAI!](https://www.raiplay.it/video/2022/02/Presa-diretta-Il-sistema-Universita---Puntata-del-07022022-bf3b1345-3af8-43c0-b477-8baf97b55370.html)",
            "[PresaDiretta!](https://www.youtube.com/watch?v=6jgN9Vcti8g)",
            "[Che resti fra noi!](https://www.youtube.com/watch?v=G4QXL6NHMi8)",
            "[Siamo su YT!](https://www.youtube.com/results?search_query=intercettazioni+universit%C3%A0+bandita)",
            "[Privilegiati? Ma no!](https://www.amazon.it/universit%C3%A0-Privilegi-baronali-gestione-truccati/dp/8832963914)"
        ]
        return choice(elements)
