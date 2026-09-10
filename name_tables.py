"""
name_tables.py — name pools for the Name Generator page.

Data-only module (no streamlit) so the ~1,100-line NAMES dict doesn't bury
the page logic in pages/NameGenerator.py. Same root-module pattern as
treasure_tables.py / random_tables.py.
"""

# ── Name Data ─────────────────────────────────────────────────────────────────
# Sources: D&D PHB, FR lore, BG3, DOS2, Dragon Age, The Witcher, Critical Role,
# Tolkien, Arthurian legend.
# Each race has "male", "female", and "surname" lists.

NAMES = {
    "Human": {
        "male": [
            # D&D / fantasy staples
            "Aaron","Aldric","Alric","Ander","Arlen","Barrett","Beren","Bram",
            "Calder","Calvin","Cedric","Colm","Corin","Corwin","Davin","Derek",
            "Dorian","Drake","Duncan","Dylan","Edmund","Edric","Emeric","Erasmus","Erwin",
            "Ethan","Ferris","Flynn","Gareth","Godric","Gordon","Grant","Grayson",
            "Hadrian","Harlan","Heath","Ivan","Jace","Jared","Jasper","Julien",
            "Kilian","Knox","Lander","Landon","Leoric","Lorne","Marcus","Martin","Matthias",
            "Miles","Morgan","Nathan","Niall","Orin","Owen","Paxton","Quinn",
            "Rafe","Ren","Rex","Rhys","Roland","Rowan","Rupert","Rylan",
            "Seth","Silas","Simon","Sterling","Theron","Tobias","Uther","Victor",
            "Wade","Werner","Wesley","Zane",
            # Arthurian
            "Arthur","Bedivere","Bors","Galahad","Gawain","Gaheris","Lamorak","Lancelot",
            "Percival","Tristram",
            # Expanded fantasy
            "Aldous","Ashton","Avon","Baird","Benedikt","Bertram","Caspian","Cromwell",
            "Darian","Deklan","Edwyn","Evander","Fabian","Gavin","Griffith","Gunthar",
            "Harold","Horace","Ignatius","Jarvis","Kendrick","Leopold","Lionel","Lucan",
            "Malcolm","Oswin","Rainier","Renwick","Roderick","Sylvester","Tarquin","Tavish",
            "Thaddeus","Ulric","Vernon","Walden","Wilhelm","Wolfric","Xander",
            # Dragon Age
            "Alistair","Anders","Cullen","Nathaniel","Blackwall",
            # The Witcher
            "Eskel","Geralt","Jaskier","Lambert","Vesemir","Sigismund","Zoltan","Cahir",
            # Critical Role
            "Caleb","Fjord","Percy","Scanlan",
            # BG3 / DOS2
            "Gale","Ifan","Minsc","Wyll",
        ],
        "female": [
            # D&D / fantasy staples
            "Ada","Adele","Alena","Alys","Amara","Amelia","Ana","Annika","Ardis",
            "Astrid","Audra","Ava","Brin","Brynja","Cara","Cate","Cerys",
            "Clare","Delia","Delphine","Diana","Edith","Eileen","Elena",
            "Elise","Ellen","Elora","Emira","Emma","Erica","Esme","Eva","Fiona",
            "Freya","Grace","Gretchen","Gwyneth","Hana","Ida","Ingrid","Irene","Isla",
            "Janna","Jessa","Joanna","Kara","Karla","Kate","Kira",
            "Lana","Lara","Leah","Lena","Liora","Lucia","Lynn","Maia","Mara","Maren",
            "Marta","Maya","Megan","Mila","Mira","Moira","Nadia","Nora",
            "Petra","Portia","Rae","Reva","Rosa","Sara","Selene","Sera","Sigrid",
            "Svea","Sylvia","Tara","Thalia","Una","Vera","Willa","Yeva","Zara",
            # Arthurian
            "Elaine","Guinevere","Isolde","Morgana","Nimue","Ragnelle",
            # Expanded fantasy
            "Adriana","Agatha","Althea","Beatrice","Belinda","Camille","Clarissa",
            "Constance","Cordelia","Dagmar","Edwina","Eleanor","Elspeth","Emmeline",
            "Evelyn","Francesca","Gabrielle","Georgina","Harriet","Helena","Hester",
            "Isabeau","Isadora","Jacinda","Katarina","Lavinia","Leonora","Louisa",
            "Lucinda","Marcella","Marguerite","Millicent","Miriam","Natalia","Octavia",
            "Priscilla","Rosalind","Rowena","Sabrina","Theodora","Valentina","Zenobia",
            # Dragon Age
            "Aveline","Cassandra","Josephine","Leliana","Morrigan","Vivienne","Wynne",
            # The Witcher
            "Ciri","Fringilla","Philippa","Triss","Yennefer",
            # Critical Role
            "Beauregard","Imogen","Laudna","Veth",
            # BG3 / DOS2
            "Karlach","Lohse",
        ],
        "surname": [
            "Alderman","Ashwick","Barron","Blackwood","Bramble","Brightwater","Coldwell","Crane",
            "Crowley","Dalton","Dunbar","Eastwood","Fairchild","Falconer","Fenn","Finch",
            "Fletcher","Forrest","Galloway","Garner","Gaunt","Grayson","Hale","Harken",
            "Hartwell","Highmore","Holbrook","Ironsides","Kingsley","Knox","Langley","Larkspur",
            "Latham","Lockwood","Maddox","Marsh","Morley","Nighthollow","Oakheart",
            "Pemberton","Quintain","Raven","Redwood","Rickard","Rowan","Sable","Silverthorn",
            "Stonebridge","Tanner","Thorne","Thornton","Underhill","Vane","Wakefield","Walcott",
            "Whitlock","Willowmere","Wyndham","Ashford","Brightwell","Cromley","Dunmore",
            "Edgewick","Farrow","Gilmore","Hathwick","Ironwood","Kelwick","Lorrimer",
            "Aldgate","Blackthorn","Brightmoor","Castlemore","Coldbrook","Copperfield",
            "Darkwater","Dunfield","Eastmere","Fairfax","Greywood","Grimshaw",
            "Halcyon","Hawkwood","Hollowell","Ivywood","Kessler","Lanark","Lightwood",
            # BG3 / FR surnames
            "Dekarios","Ravengard","Widogast","Silverhand","Stormweather","Falconhand",
        ],
    },

    "High Elf": {
        "male": [
            # PHB / D&D standards
            "Adran","Aelar","Arannis","Aramas","Aust","Beiro","Berrian","Caeldrim","Caelar",
            "Carric","Erdan","Erevan","Fivin","Galinndan","Hadarai","Heian","Himo",
            "Ivellios","Laucian","Mindartis","Naal","Nuvin","Paelias",
            "Peren","Quarion","Riardon","Rolen","Soveliss","Thamior","Tharivol","Theren","Varis",
            # Tolkien
            "Celeborn","Elrond","Glorfindel","Thranduil","Legolas","Eldarion","Elladan","Elrohir",
            # FR / Realms
            "Khelben","Methrammar","Elminster","Lamorak",
            # Critical Role
            "Vax'ildan",
            # BG3
            "Astarion",
            # Additional quality names
            "Aelithas","Aethon","Amroth","Anduil","Ardion","Arelith","Arevel",
            "Caethon","Caladrel","Calanon","Celebrant","Daeren","Eiravel","Eldaran","Eldarion",
            "Elharath","Elian","Eliovar","Elowen","Elrand","Elrath","Faeron","Faervel",
            "Galathir","Galathorn","Galaviel","Galavel","Haemar","Haeron","Haevel",
            "Iavel","Iaeron","Ioral","Ioreth","Iorvel","Irian","Iravel",
            "Laeron","Laevel","Laevon","Maeron","Maevel","Naelon","Naeron",
            "Oraenir","Oravel","Paelon","Paeron","Raelion","Raenon",
            "Saevel","Saeron","Taelon","Taeron","Thaelon","Thaeron","Vaelon","Vaeron",
            "Aedor","Aelindor","Aethindor","Caelindor","Daelindor","Faelindor",
            "Gaelon","Gaelindor","Haelindor","Iaelindor","Kaelindor","Laelindor",
            "Maelindor","Naelindor","Raelindor","Saelindor","Taelindor","Vaelindor",
        ],
        "female": [
            # PHB / D&D standards
            "Adrie","Ahinar","Althaea","Anastrianna","Andraste","Antinua","Bethrynna","Birel",
            "Caelynn","Chaedi","Claira","Dara","Drusilia","Enna","Felosial","Ielenia","Jelenneth",
            "Keyleth","Leshanna","Lia","Mialee","Myriil","Naivara","Quelenna","Quillathe",
            "Sariel","Shanairra","Shava","Silaqui","Theirastra","Thiala","Vadania","Valanthe",
            "Valna","Xanaphia","Zilvara",
            # Tolkien
            "Arwen","Galadriel","Celebrian","Luthien","Idril",
            # Critical Role
            "Vex'ahlia",
            # DOS2
            "Sebille","Saheila",
            # FR
            "Alustriel","Laeral","Liriel","Dove","Qilue",
            # Additional quality names
            "Aelindra","Aelithra","Aerindra","Aeritha","Alindra","Alistra",
            "Caelindra","Caelithra","Celebrindal","Celindra","Celithra","Daelindra",
            "Daelithra","Daerithra","Elaindra","Elanithra","Elindra","Elithra","Elithriel",
            "Faelindra","Faelithra","Gaelindra","Gaelithra","Iaelindra",
            "Laelindra","Laelithra","Maelindra","Maelithra","Naelindra","Naelithra",
            "Oraelindra","Paelindra","Raelindra","Raelithra",
            "Saelindra","Saelithra","Taelindra","Taelithra","Vaelindra","Vaelithra",
            "Aelora","Aeloria","Aeloriel","Aeris","Aethas","Aethis","Aethira",
            "Caelora","Caeloria","Daelora","Daeloria","Faelora","Faeloria",
            "Gaelora","Gaeloria","Haelora","Haeloria","Laelora","Laeloria",
            "Maelora","Maeloria","Naelora","Naeloria","Raelora","Raeloria",
            "Saelora","Saeloria","Taelora","Taeloria","Vaelora","Vaeloria",
        ],
        "surname": [
            "Amakiir","Amastacia","Galanodel","Holimion","Ilphelkiir","Liadon","Meliamne",
            "Nai'lo","Siannodel","Xiloscient",
            # Quality descriptive surnames
            "Avenleaf","Brightmantle","Crystaldawn","Dawnglade","Dawnleaf","Dawnmere",
            "Dawnweaver","Dawntracker","Elmwood","Evenstar","Everglade","Everleaf",
            "Goldleaf","Greywing","Highmantle","Lightbringer","Moonglade",
            "Moonshadow","Silverbough","Silverleaf","Silverwind","Skymantle","Starbreeze",
            "Starmantle","Starweaver","Sunmantle","Veldahar","Windwalker",
            "Brightstar","Crystalwind","Dawnsong","Dawnspire","Evenmantle","Evensong",
            "Goldwind","Moonbreeze","Moonleaf","Moonspire","Silverbreeze","Silverspire",
            "Skyleaf","Skyspire","Starsong","Starspire","Sunleaf","Sunspire","Windleaf",
        ],
    },

    "Wood Elf": {
        "male": [
            # PHB / D&D standards
            "Adran","Almer","Bryn","Caelin","Carric","Celu","Daenn","Dareth","Edran","Erdan",
            "Faell","Galath","Geth","Haleth","Harak","Harwyn","Iavel","Illian","Inialos",
            "Kael","Kaelar","Laranth","Laucan","Lio","Loranth","Lyran","Maerov","Malyr",
            "Meiral","Murrath","Naivyr","Nylin","Oronar","Piel","Rael","Riaryn",
            "Riel","Rolen","Saern","Saevel","Soveliss","Tael","Thaeron","Thariel","Vael","Varis",
            # Dragon Age
            "Fenris","Solas","Zevran","Iorveth",
            # BG3
            "Halsin",
            # Additional quality names
            "Aelduin","Aelmar","Aelryn","Aelven","Aerath","Aerith","Aerven","Belduin",
            "Belmar","Belryn","Celmar","Celryn","Daelduin","Daelmar","Daelryn","Edrath",
            "Edren","Edrin","Eldath","Elduin","Elmar","Elryn","Faelmar","Faelryn",
            "Gaelmar","Gaelryn","Haelmar","Haelryn","Laelmar","Laelryn","Maelduin",
            "Maelmar","Maelryn","Naelmar","Naelryn","Oraelmar","Oraelryn",
            "Raelmar","Raelryn","Saelmar","Saelryn","Taelmar","Taelryn","Vaelmar","Vaelryn",
            "Alduin","Aldrath","Aldren","Aldrin","Aldwyn","Almaryn","Alryn",
            "Beldrath","Beldren","Beldrin","Beldwyn","Celryn","Celrath","Caldren",
            "Daldrath","Daldren","Daldrin","Daldwyn","Edaldrath","Edaldren",
            "Faldrath","Faldren","Galdrath","Galdren","Haldrath","Haldren",
        ],
        "female": [
            # PHB / D&D standards
            "Aerin","Ailene","Alaine","Alura","Amareth","Anire","Arael","Arwyn",
            "Cael","Caelie","Caelynn","Celenne","Daein","Daeira","Dariel","Eilinel","Elria",
            "Gala","Galiela","Ilara","Imariel","Ithiria","Laeral","Lauriel","Liela","Lyara",
            "Maer","Maerel","Mira","Miranna","Naeris","Naivara","Nyriel","Oriel","Orien",
            "Raielle","Raina","Samel","Seriel","Shanir","Sharien","Silaen","Siran","Taeral",
            "Thalira","Thiala","Thiane","Vaelrin","Veil","Vylara","Zylara",
            # Dragon Age
            "Merrill","Sera",
            # DOS2
            "Sebille",
            # Additional quality names
            "Aelindra","Aelithra","Aerindra","Aeritha","Belindra","Belithra","Celindra",
            "Celithra","Daelindra","Daelithra","Daerithra","Elaindra","Elanithra",
            "Faelindra","Gaelindra","Haelindra","Laelindra","Laelithra",
            "Maelindra","Maelithra","Naelindra","Naelithra","Raelindra","Raelithra",
            "Saelindra","Saelithra","Taelindra","Taelithra","Vaelindra","Vaelithra",
            "Aldindra","Aldithra","Beldindra","Beldithra","Celdindra","Celdithra",
            "Daldindra","Daldithra","Eldindra","Eldithra","Faldindra","Faldithra",
            "Galdindra","Galdithra","Haldindra","Haldithra","Laldindra","Laldithra",
            "Maldindra","Maldithra","Naldindra","Naldithra","Raldindra","Raldithra",
        ],
        "surname": [
            "Brightwood","Deepwood","Elmshade","Forestmantle","Greenmantle","Greensward",
            "Greenthorn","Greenwood","Ironbark","Ironwood","Leafshade","Leafthorn","Leafwood",
            "Longwood","Maplewood","Mistwood","Moonwood","Oakheart","Oakleaf",
            "Oakmantle","Oakmere","Oakshadow","Oakshade","Oakthorn","Oakwood","Pinewood",
            "Riverwood","Rootwood","Rosewood","Shadowbark","Shadowleaf","Shadowmantle",
            "Shadowmere","Shadowthorn","Shadowwood","Silverwood","Swiftwood","Thornbark",
            "Thornleaf","Thornmere","Thornwood","Timberwood","Wildwood","Willowbark","Willowleaf",
            "Alderbough","Aspenbark","Birchwood","Cedarmantle","Elmroot","Fernwood",
            "Hazelwood","Ivywood","Laurelwood","Mosswood","Murkwood","Redwood",
            "Sycamoremantle","Willowmere","Yewwood",
            # Dragon Age Dalish clan names
            "Arainai","Lavellan","Mahariel","Surana",
        ],
    },

    "Drow": {
        "male": [
            # FR lore staples
            "Adas","Alton","Corin","Dinin","Drizzt","Elron","Erlyn","Gromph","Guldur",
            "Hatch","Ilven","Irae","Jarlaxle","Kelnozz","Khaless","Masoj","Milzzt",
            "Nauzhror","Neer","Niccolo","Pharaun","Pinal","Rizzen","Ryld",
            "Sorn","Tiago","Tsabrak","Uthe","Valas","Vicross","Zaknafein","Zilvra",
            # BG3 inspired
            "Rai","Vel","Xan","Zek","Orin",
            # Additional quality Drow names
            "Abban","Adhek","Ados","Aeryn","Afar","Agun","Ahrak","Ahrun","Aldron",
            "Aledan","Alran","Alrath","Alrek","Amreth","Amrok","Andrak",
            "Andreth","Ardran","Ardrek","Areth","Arkan","Arkath","Arketh","Arkhan",
            "Arnek","Arneth","Aronn","Arrak","Arreth","Arrok","Arron","Arroth","Arsak",
            "Arseth","Arsok","Arthan","Arthen","Arthon","Arvan","Arvek","Arven","Arveth",
            "Aryk","Aryth","Arzak","Berg'inyon","Bregan","Davian","Davrak","Deldrak",
            "Devrak","Dornek","Drathak","Drakesh","Elbryn","Elkan","Elrath","Ernak",
            "Faeldrak","Faeron","Fanek","Felrak","Fenrak","Filrak",
            "Galrak","Ganrak","Garrak","Gelrak","Gilrak","Golrak","Gonrak",
            "Halvrak","Hamrak","Hanrak","Helrak","Helvrak","Herrak","Hirak","Hilvrak",
            "Ilvrak","Imrak","Inrak","Irrak","Irvrak","Israk","Ithrak","Itvrak",
        ],
        "female": [
            # FR lore staples
            "Akordia","Alue","Anastrae","Arach","Aravae","Arxenia","Baelae","Briza","Callindra",
            "Charinida","Dalhia","Despana","Devara","Dhara","Elvirith","Erelda","Filrae",
            "Greyanna","Imrae","Ilharess","Jhulgra","Kailani","Liriel","Malice","Malogdra",
            "Maris","Melarue","Naerdith","Neerindra","Nifyr","Norryn","Phaere","Qilu",
            "Quenthel","Reverie","Sabal","Saszune","Triel","Urza","Vierna","Villinae","Wrae",
            "Xune","Yvonnel","Zeerith",
            # BG3
            "Minthara",
            # BG1/2
            "Viconia",
            # Additional quality Drow names
            "Aavrae","Adira","Aelrae","Aerinae","Aesrae","Ahinae","Airae","Alinae",
            "Amrae","Aninae","Anrae","Aorae","Arinae","Arrae","Asrae",
            "Atinae","Atrae","Aurae","Avrae","Azrae","Baenrae","Belrae","Caelrae",
            "Dalrae","Devrae","Elrae","Faelrae","Gaelrae","Haelrae","Jaelrae","Kaelrae",
            "Laelrae","Maelrae","Naelrae","Paelrae","Raelrae",
            "Saelrae","Taelrae","Vaelrae","Xaelrae","Yaelrae","Zaelrae",
            "Halvrae","Hamrae","Hanrae","Helrae","Helvrae","Herrae","Hirae","Hilvrae",
            "Ilvrae","Imrae","Inrae","Irrae","Irvrae","Israe","Ithrae","Itvrae",
        ],
        "surname": [
            # Established FR Drow Houses
            "Baenre","Barrison Del'Armgo","Do'Urden","Duskryn","Fey-Branche","Horlbar",
            "Hunzrin","Kenafin","Mizzrym","Srune'lett","Vandree","Xorlarrin","Zauvirr",
            # Additional house/clan names
            "Abaeir","Arachar","Arkenrith","Arluin","Arlynd","Armandre","Armark",
            "Arnulda","Arpeth","Arrak","Arren","Arrin","Arros","Arroth","Arsken",
            "Arusk","Arvain","Arveth","Arvith","Arxen","Aryen","Aryeth","Arzoth",
            "Dalael","Davlamin","Delvarin","Devlamin","Dharvek","Dilvae","Dolvane",
            "Halveth","Halvain","Halvrak","Halvael","Hamrael","Hamrath","Hamreth",
        ],
    },

    "Dwarf": {
        "male": [
            # PHB / D&D staples
            "Adrik","Alberich","Baern","Barendd","Brottor","Bruenor","Dain","Darrak","Delg",
            "Eberk","Einkil","Fargrim","Flint","Gardain","Harbek","Kildrak","Kilhern","Morgran",
            "Mulfin","Mundek","Orsik","Oskar","Rangrim","Rurik","Taklinn","Thoradin","Thorin",
            "Tordek","Traubon","Travok","Ulfgar","Veit","Vondal",
            # Tolkien
            "Balin","Bifur","Bofur","Bombur","Dori","Dwalin","Fili","Gloin","Kili","Nori","Oin","Ori",
            # Dragon Age
            "Bhelen","Oghren","Varric",
            # FR
            "Pwent",
            # Additional quality names
            "Beldrak","Belgrim","Belrak","Boltrik","Delbrak","Dolgun","Dolgrin","Dorden",
            "Durgak","Durthane","Falrik","Felrak","Fendar","Fendrin","Forgal","Furgal",
            "Golrak","Gordin","Goruk","Gothr","Granak","Grandin","Grendak","Grindak",
            "Grindin","Gurnak","Hadrak","Harnak","Helrak","Heldrak","Holgrak","Holrak",
            "Katrak","Kelrak","Kornak","Kolrak","Kolgrak","Kundrak","Kurgrim",
            "Meldrak","Melgrim","Norrak","Norgrim","Ondrak","Orgrim","Ormrak","Osrak",
            "Randrak","Rangrak","Thordrak","Thornak","Turgak","Turgrim","Valdrak","Valgrim",
            "Alrik","Andrak","Ansrak","Arkrak","Arnrak","Arrak","Arsrak","Artrak",
            "Baldrak","Balfrak","Balgrak","Balrak","Bamrak","Banrak","Barrak","Basrak",
            "Caldrak","Calfrak","Colgrak","Colrak","Cornrak","Corrrak","Cortrak",
        ],
        "female": [
            # PHB / D&D staples
            "Amber","Artin","Audhild","Bardryn","Dagnal","Diesa","Eldeth","Falkrunn","Finellen",
            "Gunnloda","Gurdis","Helja","Hlin","Kathra","Kristryd","Ilde","Liftrasa","Mardred",
            "Riswynn","Sannl","Torbera","Torgga","Vistra",
            # Dragon Age
            "Sigrun",
            # Additional Nordic/dwarf names
            "Alfhild","Alvhild","Astrid","Berta","Bretta","Brunhilda","Dagny","Daria",
            "Dotta","Drifa","Duria","Edda","Embla","Erla","Finna","Freydis",
            "Gard","Gerda","Grimhild","Gudrun","Gurda","Herborg","Hilda","Holda",
            "Ingrid","Kara","Katla","Kira","Magna","Marta","Mattea","Munin","Nessa","Odda",
            "Ragna","Randi","Sif","Sigrid","Siri","Skadi","Solvi","Thora","Toril",
            "Ulla","Unn","Urd","Vigdis","Vilda","Volla","Yrsa",
            "Aldis","Alfrun","Almrun","Alvsig","Anndis","Arndis","Arndra",
            "Bergdis","Berghild","Bergrid","Borghild","Borgrid",
            "Dagrid","Eldrid","Geirrid","Geirdis","Gudrid",
            "Haldis","Halrid","Helga","Heldis","Helrid",
            "Ingdis","Ingrid","Ingrun","Ingthor","Kadis","Katdis","Katrid","Kolgrid",
            "Mardis","Margrid","Sigdis","Sigrun","Sigrid","Solveig","Tordis","Torgrid",
            "Ulfdis","Ulfrid","Urdis","Valgerd","Vordis","Vorrid",
        ],
        "surname": [
            # PHB clan names
            "Balderk","Dankil","Gorunn","Hamarakkam","Loderr","Lutgehr","Rumnaheim","Strakeln",
            "Torunn","Ungart",
            # Dragon Age
            "Tethras",
            # Compound surnames
            "Anvilstrike","Battlehammer","Boulderback","Bouldershoulder","Brightstone",
            "Copperbeard","Copperkettle","Deepdelver","Deepmine","Diamondback",
            "Dustkeg","Fireforge","Flinteye","Foehammer","Gemcutter","Goldbeard",
            "Goldhammer","Goldvein","Hammerfall","Hammerstone","Ironbar","Ironfoot",
            "Ironforge","Ironfist","Ironcrown","Ironhammer","Mountainheart","Orecrown",
            "Rockfist","Stoneback","Stonebow","Stonemight","Thunderseeker",
            "Underbrew","Weatherskin","Axefall","Brazenback","Deepkeg","Diamondforge",
            "Flameforge","Gildedkeg","Goldenaxe","Hammerback","Ironmane",
            "Oakhammer","Runescar","Silveraxe","Steelback","Stormhammer","Stonekeg",
        ],
    },

    "Halfling": {
        "male": [
            # PHB / D&D staples
            "Alton","Ander","Cade","Corrin","Eldon","Errich","Finnan","Garret","Lindal","Lyle",
            "Merric","Milo","Osborn","Perrin","Reed","Roscoe","Wellby",
            # Tolkien
            "Bilbo","Drogo","Frodo","Merry","Pippin","Sam","Samwise","Tobold",
            # Critical Role
            "Orym","Scanlan",
            # Additional good halfling names
            "Aldemar","Aldous","Alford","Alwin","Anders","Barnabas","Benny","Bertram",
            "Bilford","Bobbin","Bram","Cally","Corbin","Dalvin","Dodger",
            "Dorn","Dorril","Elm","Elmo","Emric","Ennis","Errand","Fitch","Ford",
            "Garlen","Gill","Glyn","Grenn","Grove","Hammo","Hardy","Harkin",
            "Hart","Harvey","Hollis","Jinks","Jorlin","Kell","Kent","Kirk",
            "Larkin","Lawson","Lenny","Lewis","Lotho","Luco","Lukas","Mack",
            "Ned","Norman","Odo","Odric","Otto","Paddy","Pence","Penn","Perry",
            "Pip","Platt","Rand","Rob","Robin","Rocky","Rodric","Ron","Ross",
            "Sandy","Slim","Sprout","Tad","Tib","Toby","Todd","Tuck","Tully",
            "Woody","Yule","Zack","Alfie","Archie","Barney","Bernie","Bilford",
            "Bramwell","Bucky","Corbett","Crickett","Danby","Digby","Durbin",
            "Edbert","Ellery","Emery","Fenny","Ferby","Finley","Fletch",
            "Garfield","Garvey","Gilberd","Goodwin","Gordy","Gus","Hackett",
        ],
        "female": [
            # PHB / D&D staples
            "Andry","Bree","Callie","Cora","Euphemia","Jillian","Kithri","Lavinia","Lidda",
            "Merla","Nissa","Portia","Seraphina","Shaena","Trym","Vani","Verna","Wenna",
            # Tolkien
            "Lobelia","Rosie","Ruby",
            # Critical Role
            "Veth",
            # Additional good halfling names
            "Alma","Amara","Beatrix","Bella","Bett","Birdy","Blossom","Bonny","Briar","Brin",
            "Cherry","Clover","Daffy","Daisy","Damaris","Delia","Della","Dilly","Dimple",
            "Dotty","Dovie","Elanor","Emer","Emmy","Essa","Fancy","Fanny","Feather","Fleur",
            "Flora","Flower","Freda","Garnet","Gemma","Gilda","Ginny","Goldie",
            "Gracie","Hilda","Holly","Honey","Ila","Iris","Ivy","Jenna","Jenny","Joanie",
            "Josie","Kitty","Lavender","Lily","Lona","Lorie","Lyra","Mabel",
            "Maisy","Marni","Matty","Maude","Maura","Meg","Merri","Millie","Minnie",
            "Misty","Molly","Myrtle","Nellie","Nelly","Nixie","Pansy","Pearl","Penny",
            "Peony","Poppy","Posie","Prima","Prim","Quinn","Rose","Sadie",
            "Sally","Sasha","Shantell","Tilly","Trudy","Violet","Winnie","Zena",
            "Adelie","Birdie","Blossom","Clementine","Cordelia","Cornelia","Dotsy",
            "Effie","Elspet","Emmeline","Eudora","Florabel","Florrie","Greta","Harriet",
            "Hattie","Hetty","Honoria","Isadora","Jessamine","Juniper","Lottie",
        ],
        "surname": [
            "Brushgather","Goodbarrel","Greenbottle","Highhill","Hilltopple","Leagallow",
            "Tealeaf","Thorngage","Tosscobble","Underbough",
            # Tolkien
            "Baggins","Brandybuck","Cotton","Gamgee","Sackville","Took",
            # Additional halfling surnames
            "Barleycorn","Brightstream","Buckhollow","Burrows","Clayhill","Cobble",
            "Copperkettle","Dustmantle","Fernhollow","Goodfoot","Greenpenny",
            "Hamsfoot","Haystack","Hedgerow","Hilltop","Holloway","Honeygulch","Honeythorn",
            "Huckleberry","Ironfeet","Leafwhisper","Littleleaf","Lowland","Luckystone",
            "Meadows","Merriweather","Moonshadow","Nibblefingers","Oakenheel","Picklefoot",
            "Primrose","Quickfoot","Quickstep","Reedwhistle","Riverbank","Rockbottom",
            "Rootberry","Rosebud","Sandybanks","Shortwick","Silkfoot","Smallbone","Smallwood",
            "Softfoot","Stoutfoot","Sweetbriar","Tanglethorn","Thistledown","Thornbriar",
            "Underhill","Warmstone","Whiskerwick","Willowgrove","Wanderfoot","Wheatfield",
            "Tumbledown","Applebottom","Barrowfoot","Cloverfield","Crickhollow","Ferndale",
            "Foxburrow","Gladehollow","Hopgarden","Millstone","Nettlebrook","Pebbleford",
            "Rushmore","Sedgeback","Thistlewick","Willowmarch",
        ],
    },

    "Gnome": {
        "male": [
            # PHB / D&D staples
            "Alston","Alvyn","Boddynock","Brocc","Burgell","Dimble","Eldon","Erky","Fonkin",
            "Frug","Gerbo","Gimble","Glim","Jebeddo","Kellen","Namfoodle","Orryn","Roondar",
            "Seebo","Sindri","Warryn","Wrenn","Zook",
            # BG3 gnomes
            "Barcus","Wulbren",
            # Additional quality gnome names
            "Alson","Barnabas","Benny","Bobbin","Brewster","Brin",
            "Burnick","Capper","Castor","Chipper","Dapper","Dink",
            "Dippet","Fizz","Fizzwick","Flick","Flinn","Flipper","Flit","Frizzle",
            "Gearwick","Gizmo","Glimmer","Grin","Grit","Grub",
            "Higgle","Hoppish","Imp","Jangle","Jingles","Jinx","Kibble","Kipper",
            "Knack","Krinkle","Lenny","Linx","Lockwick","Merrik","Nib","Nimblewit",
            "Pebble","Pepwick","Pip","Plink","Pop","Puddle","Puff","Putter",
            "Ratchet","Rip","Riv","Spark","Sprocket","Tink","Tinkle","Tinker","Wisk",
            "Wobble","Wrick","Wyle","Zapwick","Zipper","Zipwick","Zork",
            "Addock","Alver","Bimble","Bisby","Bixby","Bloke","Bogle","Bonk","Boppet",
            "Brack","Brimble","Brisket","Brownie","Bubble","Buckle","Bumble",
            "Cog","Cogsworth","Crinkle","Crispy","Dabble","Dibble","Diggle","Dimple",
            "Doddle","Doggle","Doink","Dongle","Doodle","Drizzle","Drobble",
            "Fangle","Farble","Fender","Fib","Fiddle","Figgle","Fingle","Fip","Fipple",
        ],
        "female": [
            # PHB / D&D staples
            "Bimpnottin","Breena","Caramip","Carlin","Donella","Duvamil","Ella","Ellyjobell",
            "Ellywick","Lilli","Loopmottin","Lorilla","Mardnab","Nissa","Nyx","Oda","Orla",
            "Roywyn","Shamil","Tana","Waywocket","Zanna",
            # Additional quality gnome names
            "Ada","Addie","Alana","Ally","Alma","Amber","Amelia","Andie","Bixby",
            "Bonnie","Briar","Brin","Brixie","Brooke","Button","Candy","Carrie",
            "Cherry","Clover","Cora","Cricket","Dee","Della","Dill","Dimples",
            "Dot","Ellie","Emmy","Fancy","Fauna","Fern","Fifi","Fizz","Fleur",
            "Flora","Flutter","Frannie","Frizz","Gale","Gem","Gilda","Gilly","Goldie",
            "Gracie","Gwen","Hazel","Heather","Holly","Honey","Hope","Iris","Ivy","Izzy",
            "Jelly","Jess","Jingle","Jinx","Jodie","Joy","June","Juniper","Kit","Kitty",
            "Lacy","Lara","Lavender","Leafy","Lily","Lina","Linx","Lolly","Lottie",
            "Lucky","Luna","Merry","Misty","Nessa","Nixie","Penny","Pixie","Poppy",
            "Prim","Rivi","Rosie","Shimmer","Sparkle","Sprocket",
            "Sunny","Tilly","Tinker","Wink","Zippi","Zippy",
            "Bimbly","Bindle","Binky","Birdie","Bitsie","Bixby","Bobble","Boffin",
            "Bonbon","Boodle","Bounce","Bramble","Breezy","Brioche","Bubble","Bumble",
            "Chime","Cinder","Clover","Comet","Copper","Crinkle","Crumble",
            "Dainty","Daisy","Dazzle","Dew","Dimple","Dinkle","Ditzy","Doodle",
        ],
        "surname": [
            # PHB / D&D staples
            "Beren","Daergel","Folkor","Garrick","Nackle","Murnig","Ningel","Raulnor",
            "Scheppen","Timbers","Turen",
            # Additional quality gnome surnames
            "Bumblewort","Clatterspring","Cogsworth","Copperkettle","Copperwhistle",
            "Crankshaft","Crickhollow","Dinklewick","Fiddlestick","Geargrind",
            "Gearwick","Gigglestep","Gogglesnap","Goldpocket","Goldtinkle","Jollywhisker",
            "Kettledrum","Nimbletoes","Pocketwatch","Pocketwhistle","Quickfinger",
            "Quickspanner","Ratchet","Rattlecog","Silverpenny","Silverspring","Smallgear",
            "Springclock","Steelspring","Thistlefizz","Ticktock","Tinklewood",
            "Topknot","Whistlespark","Whistlewick","Whirligig","Wibbleclock",
            "Wobblecog","Boltbrain","Coppercog","Crankarm","Flickerwick","Frostcoil",
            "Blinkspring","Bouncecog","Brightcog","Brightspring","Bubblecog","Burnspring",
            "Clinkspring","Clatterbell","Copperpenny","Crankbell","Crinklebell",
        ],
    },

    "Half-Orc / Orc": {
        "male": [
            # PHB / D&D staples
            "Arng","Aruget","Bherg","Brarg","Brugg","Crull","Darg","Dorn","Drak","Drog",
            "Feng","Galg","Garg","Gork","Grak","Grath","Grish","Grom","Grosh","Groth",
            "Grudge","Grum","Grun","Guth","Harg","Haruk","Horg","Hrun","Hugur","Hurk",
            "Jork","Karg","Kharag","Kharash","Khash","Kolk","Krag","Krom","Krug","Larg",
            "Lorm","Lurk","Marg","Mash","Morg","Mork","Morog","Narg","Nork","Okk","Org",
            "Prak","Rarg","Roth","Rug","Rugg","Rulg","Rurg","Sarg","Skar",
            "Skrag","Skurn","Snog","Snorg","Tharg","Thork","Thugg","Torg","Trak","Trog",
            "Truk","Urg","Urk","Varg","Varn","Vog","Vorg","Vrak","Yarg","Yorg",
            "Zarg","Zog","Zorg","Bork","Brak","Bruk","Burkh",
            # Tolkien orcs
            "Azog","Bolg","Gothmog","Lugdush","Mauhur","Muzgash","Radbug","Shagrat",
            "Ugluk","Gorbag","Grishnakh","Lagduf","Snaga","Yazneg","Azgarn",
            # Additional distinct orc names
            "Gurash","Karash","Tarash","Vorak","Zorak","Bolar","Golar","Kolar","Nolar",
            "Agroth","Bahrak","Balgrim","Balrak","Bargrak","Barnak","Barrak","Batrak",
            "Bergrak","Binrak","Birrak","Bolrak","Borrak","Brakrak","Branak","Brandrak",
            "Brodrak","Bronak","Burak","Burnak","Dalrak","Dargrak","Darkrak","Darnak",
            "Delrak","Dergrak","Dernak","Dorgrak","Dornak","Drarak","Drerak","Drograk",
        ],
        "female": [
            # PHB / D&D staples
            "Aasha","Agna","Agra","Archa","Arsha","Basha","Bolga","Brasha","Bratta",
            "Brega","Brenna","Brona","Burga","Chorga","Cragga","Darasha","Darka",
            "Dessa","Doma","Draka","Drega","Durga","Dursha","Falga","Farga","Fraga",
            "Frasha","Garka","Garsha","Gasha","Grasha","Gritha","Grona","Harsha","Hasha",
            "Horra","Hurga","Isha","Joga","Karka","Kraga","Krasha","Krega","Larka",
            "Lasha","Loga","Lorga","Marka","Marsha","Megda","Mokka","Morga","Naga","Narka",
            "Okka","Orcha","Rega","Roma","Romka","Ronga","Sarka","Sharka","Shasha",
            "Torka","Torsha","Traga","Urga","Varsha","Veka","Vika","Warka","Washa",
            "Zarka","Zasha","Borga","Bracha","Bratha","Bulga","Chakka","Crasha",
            # Additional distinct names
            "Agba","Azara","Dorga","Golga","Grimsha","Gulna","Gurna",
            "Hagra","Halvra","Harva","Helga","Hroka","Hulga","Karga","Karva",
            "Marga","Morva","Narva","Orva","Rogra","Rokka","Rolga",
            "Rorra","Shalga","Shalva","Sharva","Shorka","Snarka","Turga","Ulga","Ursha",
            "Agrasha","Bagrasha","Balgha","Balkha","Barsha","Batsha","Bergsha","Binsha",
            "Birsha","Bolsha","Borsha","Braksha","Bransha","Bransha","Brodsha","Brondsha",
            "Buksha","Bursha","Dalsha","Dargsha","Darksha","Darsha","Delsha","Dergsha",
        ],
        "surname": [
            "Bloodaxe","Bonesmasher","Darkmantle","Doomfist","Duskclaw","Earthtrembler",
            "Fangbreaker","Gorehand","Grimblade","Grimborn","Grimhide","Grimjaw","Grimtooth",
            "Headcracker","Ironarm","Ironback","Ironbelly","Ironclaw","Ironjaw",
            "Ironleg","Ironmaw","Ironshoulder","Ironskin","Irontooth","Jawbreaker","Manhunter",
            "Nightstalker","Onescar","Painbringer","Rageborn","Ravenscar","Redaxe","Redclaw",
            "Redfang","Redhide","Redscar","Scarback","Skullbreaker","Skullcrusher","Skullsplitter",
            "Skullsmasher","Slaughterclaw","Soulcrusher","Spikearm","Stoneclaw","Stonefist",
            "Toothbreaker","Tuskrunner","Warborn","Warfang","Warhide","Warjaw","Warmaw","Warscream",
            "Axeborn","Bonecracker","Boneshatter","Brokenhorn","Coldblade","Coldaxe",
            "Darkfang","Deathclaw","Deathjaw","Deathmaw","Deathtooth","Deepaxe",
        ],
    },

    "Tiefling": {
        "male": [
            # PHB — Infernal names
            "Akmenos","Amnon","Barakas","Damakos","Ekemon","Iados","Kairon","Leucis","Melech",
            "Mordai","Morthos","Pelaios","Skamos","Therai",
            # BG3
            "Zevlor",
            # Critical Role
            "Mollymauk",
            # PHB virtue/vice names and name-like picks
            "Ash","Asher","Arix","Azzor","Bane","Barak","Bren","Brix","Calx",
            "Cinder","Crag","Craven","Dagger","Darke","Dax","Echor",
            "Ember","Erebus","Exile","Fang","Forge","Fury","Gloom","Grim","Grudge",
            "Haze","Hex","Ignix","Ire","Jax","Kolt","Lore","Malice","Malus","Mire",
            "Mord","Nox","Null","Omen","Peril","Pitch","Primal","Rage",
            "Rancor","Raven","Raze","Rend","Riven","Ruin","Sable","Scorch","Shade","Shard",
            "Sin","Smite","Spite","Storm","Strife","Styx","Vex","Vile","Void","Wrath","Zeal",
            # Additional distinct tiefling names
            "Abraxas","Acheron","Aeon","Azrael","Belial","Carneth","Daemon","Draven",
            "Erebon","Helion","Kaelen","Malachar","Malek","Neron",
            "Pyros","Ravakai","Ravenoth","Rymer","Serath","Sirath","Sorath","Talek",
            "Varak","Veloth","Vorath","Xenith","Xerath","Zarek","Zaros","Zarak",
            "Aldraxx","Ankareth","Arkaxx","Arvel","Askareth","Asval","Atvel",
            "Azkareth","Azval","Balraxx","Belkaxx","Braxxel","Brennaxx","Brevaxx",
            "Calkaxx","Carvaxx","Celkaxx","Cervaxx","Corkaxx","Corvaxx","Darkaxx",
        ],
        "female": [
            # PHB — Infernal names
            "Akta","Anakis","Bryseis","Criella","Damaia","Ea","Kallista","Lerissa","Makaria",
            "Nemeia","Orianna","Phelaia","Rieta","Seska","Tarika","Zelika",
            # BG3
            "Karlach","Mol",
            # PHB virtue/vice names
            "Aura","Bliss","Blaze","Brand","Calamity",
            "Cipher","Cinder","Crimson","Curse","Dark","Decay","Desire",
            "Despair","Doom","Dread","Embrace","Envy","Exile","Fate","Fell",
            "Flame","Gloom","Grave","Greed","Hex","Hope","Horror","Hunger",
            "Ire","Jade","Lament","Lash","Lore","Lust","Mara","Malice","Malign","Massacre",
            "Mire","Mirage","Misery","Mourn","Murk","Night","Nightmare",
            "Nox","Null","Omen","Pain","Pall","Peril","Pitch","Plague","Poison",
            "Pyre","Rage","Rancor","Ravage","Raven","Raze","Rend","Ruin","Sable","Sorrow",
            "Spite","Storm","Strife","Torment","Vex","Vile","Void","Woe","Wrath","Zeal",
            # Additional distinct tiefling names
            "Aevyn","Aisha","Azura","Caelith","Calypso","Cerith","Damaris",
            "Ezindra","Faevyn","Galith","Haevyn","Iaelith","Jaelith","Kaelith",
            "Laelith","Lilavith","Maelyth","Naelith","Onyxia","Ophelia","Paelith",
            "Pyrith","Raelith","Saelith","Skarith","Taelith","Vaelith",
            "Vayla","Velith","Vorath","Xaelith","Yaelith","Zaelith","Zarith",
            "Aldraxxa","Ankarethia","Arkaxxa","Arvelith","Askarethia","Asvalith","Atvelith",
            "Azkarethia","Azvalith","Balraxxa","Belkaxxa","Braxxa","Brennaxxa","Brevaxxa",
        ],
        "surname": [
            "Balmorrow","Bloodmoon","Brightfire","Burnscale","Cinders","Coldflame","Crimsonveil",
            "Darkfire","Darkflame","Darkscale","Darksoul","Darkwing","Dawnfire",
            "Demonborn","Demonflame","Demonhide","Demonscale","Demonsoul",
            "Doomfire","Embersoul","Firewrath","Flamecurse","Hellborn","Hellfire","Hellflame",
            "Hellscale","Hellsoul","Hellwrath","Infernalmark","Nightfire","Nightflame",
            "Nightscale","Nightsoul","Nightwrath","Shadowfire","Shadowflame","Shadowscale",
            "Shadowsoul","Shadowwrath","Soulfire","Soulflame","Soulscale","Soultaint",
            "Soulwrath","Taintfire","Taintflame","Taintscale","Taintsoul",
            "Taintwrath","Voidfire","Voidflame","Voidscale","Voidsoul","Voidwrath",
            # BG3
            "Cliffgate","Ravengard",
        ],
    },

    "Dragonborn": {
        "male": [
            # PHB / D&D staples
            "Arjhan","Balasar","Bharash","Donaar","Ghesh","Heskan","Kriv","Medrash","Mehen",
            "Nadarr","Pandjed","Patrin","Rhogar","Shamash","Shedinn","Tarhun","Torinn","Vraath",
            # Additional quality Dragonborn names
            "Araan","Arend","Areth","Argas","Arguul","Arian","Ardaan","Ardas",
            "Argaan","Arkaan","Arkan","Arkash","Arkon","Arkoth","Arnaan","Arnak","Arnath",
            "Arquaan","Arrak","Arrath","Arraul","Arred","Arrish","Arros","Arroth","Arsaan",
            "Arsal","Arshan","Arsuk","Artaan","Artal","Artash","Artham","Arthan","Arthon",
            "Arthos","Arvan","Arvash","Arvin","Arvok","Arwaan","Arwash","Arwin",
            "Balaan","Balash","Balath","Balek","Balesh","Baler","Balaash",
            "Donash","Doraan","Dorash","Dorath","Dorek","Doreth","Dorer","Ghash","Gheral",
            "Hesrath","Hestaan","Krivan","Krivos","Krivaan","Krivash",
            "Mehash","Mehaan","Nadarash","Nadrak","Patrek","Patraan","Rhogan","Rhosh",
            "Shamaan","Sharath","Tarhaan","Tarhan","Toraan","Torak","Vrash","Vrath",
            "Barrash","Boltash","Bordaan","Borrash","Brannash","Brandaan","Brashaan",
            "Calrash","Caraan","Carash","Carath","Carek","Careth","Carer","Cargan",
            "Darnash","Dorrash","Draatash","Dragaan","Dragrash","Drakaan","Dralaash",
        ],
        "female": [
            # PHB / D&D staples
            "Akra","Biri","Daar","Farideh","Harann","Havilar","Jheri","Kava","Korinn","Mishann",
            "Nala","Perra","Raiann","Sora","Surina","Thava","Uadjit","Vreva","Waiti","Yrara",
            # Additional quality Dragonborn names
            "Aara","Aash","Aavar","Aavash","Acra","Acsha","Adan","Adash","Adaya","Adhra",
            "Adir","Adiraa","Adiya","Adraa","Adral","Adran","Adrish","Adrosh","Aduun",
            "Aegar","Aegas","Aelash","Aenara","Aendra","Aenish","Aerash","Aerin","Aesh",
            "Aeshin","Afar","Afara","Baara","Baash","Baavar","Baavash","Babin","Babir",
            "Dabira","Dacra","Daisha","Dakar","Dala","Dalaa","Dalak","Dalash","Dalara",
            "Dalaya","Dalbin","Dalbir","Kasha","Kavara","Korin","Mishara","Naraan",
            "Raash","Ravan","Sooraa","Sorak","Thaash","Thavan","Urak","Vraan","Vrava",
            "Barraa","Boltaa","Bordaa","Borraa","Brannaa","Brandaa","Brashaa",
            "Calraa","Caraa","Caradaa","Caravaa","Caravish","Caravith","Caravoth",
            "Darnaa","Dorraa","Draataa","Dragaa","Dragraa","Drakaa","Dralaaa",
        ],
        "surname": [
            # Traditional Draconic surnames
            "Clethtinthiallor","Daardendrian","Delmirev","Drachedandion","Fenkenkabradon",
            "Kepeshkmolik","Kerrhylon","Kimbatuul","Linxakasendalor","Myastan","Nemmonis",
            "Norixius","Ophinshtalajiir","Prexijandilin","Shestendeliath","Turnuroth",
            "Verthisathurgiesh","Yarjerit",
            # English-style descriptive surnames
            "Brightscale","Copperscale","Darkwing","Dawnscale","Deepfire","Dragonheart",
            "Fierewing","Goldscale","Ironscale","Nightfire","Redclaw","Scaledark",
            "Scaledawn","Scalefire","Silverscale","Stormbane","Stormscale","Thunderclaw",
            "Thunderwing","Emberclaw","Frostscale","Gemscale","Infernoscale","Jadescale",
            "Obsidianscale","Rubyflame","Sapphirescale",
        ],
    },

    "Goblin": {
        "male": [
            "Blix","Brix","Brog","Buk","Clag","Clank","Clek","Clog","Crake","Crink","Crog",
            "Cronk","Dak","Dap","Darg","Dex","Dink","Dip","Dirg","Dok","Dorg","Drax",
            "Drix","Drog","Drop","Dunk","Durk","Fang","Farg","Fex","Filch",
            "Fix","Fob","Fog","Fok","Fork","Frex","Frix","Frob","Frog","Funk","Gak",
            "Gap","Gark","Gex","Gink","Gix","Glak","Glib","Glik","Glob",
            "Glok","Gonk","Gorb","Gork","Gort","Grak","Grib","Grick","Grip","Grix",
            "Grob","Grog","Gronk","Gugg","Gurk","Guzz","Hak","Hap","Harg","Hat","Hex",
            "Hink","Jak","Jik","Jink","Kag","Kap","Karg","Kat","Kex","Kink","Klag",
            "Klib","Klik","Klob","Klok","Konk","Koop","Korb","Kork","Krag","Krib","Krick","Krig",
            "Larg","Lob","Lok","Lork","Lurk","Mak","Marg","Mash","Mick","Mig","Mink","Mog",
            "Nack","Nag","Nark","Nib","Nig","Nip","Nix","Nob","Nog","Noop","Nop",
            "Ork","Pak","Parg","Pat","Pex","Pig","Pik","Pix","Plim","Pop","Pot","Puff",
            "Quig","Rag","Rarg","Rat","Rek","Rib","Rick","Rip","Riv","Rob","Rok","Rork",
            "Sak","Sarg","Skar","Skrag","Skurn","Snog","Snorg","Sop","Sork","Spig","Sprik",
            "Targ","Thig","Tib","Tik","Tilk","Tok","Tork","Trak","Trig","Trok",
            "Ulg","Unk","Urk","Vak","Varg","Vek","Vix","Wig","Wik","Wink","Wok","Worg",
            "Xak","Yag","Yarg","Yorg","Zag","Zarg","Zark","Zog","Zorg","Zux",
        ],
        "female": [
            "Basha","Bix","Blag","Blat","Blix","Blot","Bogla","Bonk","Brixa","Brog",
            "Burpa","Clag","Claxa","Crix","Croba","Croka","Cronka","Daksha","Darga","Dasha",
            "Dexa","Dinsha","Dixa","Draga","Drixa","Droba","Droxa","Durrka","Farga","Fasha",
            "Fexa","Filcha","Fixa","Fobla","Foga","Fokla","Forka","Frexa","Frixa","Froba",
            "Froga","Gaksha","Garka","Gatsha","Gexa","Ginka","Gixa","Glibla","Gliksha",
            "Globa","Gloka","Glonka","Gonka","Gorba","Gorka","Gorta","Graksha","Griba",
            "Gricka","Grika","Gripa","Grixa","Groba","Groga","Gronka","Grooka","Grora",
            "Grota","Gugla","Gurka","Guzla","Haksha","Harka","Hatsha","Hexa",
            "Hinka","Hixa","Jaksha","Jika","Jinka","Kagla","Kaksha","Karka","Katsha",
            "Kexa","Kinka","Kixa","Klaksha","Klibla","Kliksha","Kloba",
            "Larga","Loka","Lorga","Marka","Marsha","Morga","Narka",
            "Okka","Orga","Rega","Roka","Sarka","Sharka","Shasha","Torka","Ulga","Vika",
            "Warka","Xaka","Yarka","Zarka","Zasha","Zorka",
        ],
        "surname": [
            "Bilebrood","Blacktoe","Bogsnout","Bonegrinder","Clawback","Clawfoot","Dirtsniff",
            "Dirtpaw","Dirtsnout","Earpicker","Eyepicker","Eyepoker","Eyestabber","Firepoke",
            "Foulbreath","Gibbersnatch","Greasepaw","Grubfinger","Gutpuncher","Jawripper",
            "Kneebiter","Kneecapper","Muckface","Muckpaw","Mudface","Mudpaw","Nosepicker",
            "Nosepoker","Pawripper","Rotgut","Scabpicker","Skullsmasher","Snotface",
            "Snotpaw","Stinkbreath","Stinkfoot","Stinkpaw","Toepicker","Wartface","Wartpaw",
        ],
    },

    "Kobold": {
        "male": [
            "Arix","Bink","Biri","Bix","Brik","Cax","Crax","Dak","Dix","Drak","Drax",
            "Fik","Fix","Frik","Gak","Gik","Grax","Grix","Hak","Hex","Hix","Jak",
            "Kak","Kek","Kix","Krax","Krix","Lak","Lek","Lik","Lox","Mak","Mek","Mix","Mox",
            "Nak","Nek","Nex","Nix","Pak","Pax","Pek","Pex","Pik","Pix","Prax","Prik",
            "Rax","Rex","Rix","Rok","Rox","Sak","Sek","Six","Slik","Slak","Snix","Snik",
            "Srak","Srex","Srik","Srox","Srix","Tak","Tek","Tik","Tix","Trak","Trex","Trik","Trok",
            "Trox","Urak","Urk","Vak","Vek","Vix","Vrak","Vrex","Vrik","Vrox","Vrix",
            "Wak","Wek","Wix","Xak","Xek","Xik","Yak","Yex","Yik","Yix","Zak","Zek","Zix",
            "Bak","Bek","Brax","Brek","Crak","Crek","Drek","Frak","Frek","Grak","Grek",
            "Snap","Snip","Skrix","Skrak","Skrik","Trixx","Vrikk","Yikk","Zrikk",
        ],
        "female": [
            "Aksha","Arsha","Bixa","Braka","Craxa","Daksha","Dasha","Dixa","Draka","Draxa",
            "Fika","Fixa","Frika","Gaka","Gika","Graxa","Grixa","Haka","Hexa","Hixa","Jaka",
            "Kaka","Keka","Kixa","Kraxa","Krixa","Laka","Leka","Licka","Lika","Loxa",
            "Maka","Meka","Mixa","Moxa","Naka","Neka","Nexa","Nixa","Paka","Paxa","Peka","Pexa",
            "Pika","Pixa","Praxa","Prika","Raxa","Rexa","Rixa","Roka","Roxa","Saka","Seka",
            "Sixa","Slika","Slaka","Snixa","Snika","Sraka","Srexa","Srika","Sroxa","Srixa",
            "Taka","Teka","Tika","Tixa","Traka","Trexa","Trika","Troka","Troxa",
            "Uraka","Urka","Vaka","Veka","Vixa","Vraka","Vrexa","Vrika","Vroxa","Vrixa",
            "Waka","Weka","Wixa","Xaka","Xeka","Xika","Xixa","Yaka","Yexa","Yika","Yixa",
            "Zaka","Zeka","Zixa","Zraka","Zrexa","Zrika","Zroxa","Zrixa",
            "Baka","Beka","Braxa","Breka","Craka","Creka","Dreka","Fraka","Graka","Hraka",
        ],
        "surname": [
            "Brightscale","Copperclaw","Dirtclimber","Dustclaw","Dustscale","Gemdigger",
            "Gemscale","Goldhider","Goldscale","Ironscale","Jadescale","Lairkeeper","Nestguard",
            "Oreseeker","Pressedscale","Redscale","Rockclimber","Rockclaw","Rockscale",
            "Rubyscale","Sandscale","Scuttleclaw","Shinyseeker","Silkscale","Silverscale",
            "Skitterfoot","Smokescale","Softscale","Swiftclaw","Swiftscale","Tinderscale",
            "Tunnelclaw","Tunnelscale","Vaultguard","Yellowscale",
        ],
    },

    "Aasimar": {
        "male": [
            # PHB / D&D staples
            "Aeron","Alaric","Aldric","Ameryn","Amos","Angelas","Aniel","Aradon","Aramus",
            "Ardath","Ardan","Ardec","Ardeth","Arel","Arelt","Aren","Arend","Areon","Aresk",
            "Arfon","Arhan","Arik","Arilan","Arimas","Arion","Arjun","Arkith","Arlan",
            "Arloc","Arlon","Arnath","Aron","Aronel","Aroneth","Aroth","Aroval","Arpeth",
            "Arrac","Arrath","Arris","Arrisel","Arrok","Arroth","Arsel","Arseth","Arsis",
            "Arsith","Artho","Arthos","Arton","Aruth","Arvath","Arven","Arvon","Arweth",
            # Angel-derived names
            "Auriel","Auris","Aviel","Aziel","Bastiel","Castiel","Celiel","Damiel","Danael",
            "Darel","Dariel","Deniel","Deriel","Doriel","Duriel","Eliel","Enriel","Etriel",
            "Gadriel","Galiel","Gatiel","Gaviel","Geriel","Goriel","Guriel",
            "Hadriel","Haniel","Hariel","Haruel","Hidriel","Iariel","Imriel","Iriel",
            "Isriel","Jodriel","Juriel","Kamiel","Katriel","Lariel","Maliel","Nariel",
            "Oriel","Pariel","Qadiel","Radiel","Sariel","Tariel","Uriel","Variel","Zariel",
            "Aelriel","Aeriel","Afiel","Agiel","Ahiel","Aiel","Airiel","Ajiel","Akiel",
            "Alriel","Amiel","Aniel","Aoriel","Apriel","Aqiel","Ariel","Asriel","Atriel",
        ],
        "female": [
            # PHB / D&D staples
            "Adara","Adaria","Adela","Aela","Aeris","Aethora","Alara","Alariel","Alena",
            "Aleria","Alesta","Aliara","Aliel","Alindra","Alira","Aliria","Aloria","Alria",
            "Altara","Alura","Amara","Amaria","Amariel","Amaris","Amaura","Ambra","Amera",
            "Amira","Amiriel","Amoria","Anara","Anaria","Anaris","Anelia","Aneria","Aniel",
            "Anindra","Anira","Aniria","Anloria","Anmara","Anora","Anuria","Aranel","Aranis",
            "Arana","Arela","Arelia","Arena","Arenia","Aresta","Arethia",
            "Ariel","Ariela","Arielle","Arienda","Arindra","Arinia","Ariola","Ariora","Arisa",
            "Arista","Aristia","Aritha","Ariya",
            # Angel-derived names
            "Celeste","Celestia","Dawniel","Elariel","Elaryn","Gloriel","Hanniel",
            "Lauriel","Luminel","Miriel","Naeriel","Radiel","Sariel","Soliel","Stariel","Uriel",
            # Additional quality names
            "Aelindra","Aelithra","Aerindra","Aeritha","Caelindra","Caelithra",
            "Daelindra","Elaindra","Faelindra","Gaelindra","Haelindra","Laelindra",
            "Maelindra","Naelindra","Raelindra","Saelindra","Taelindra","Vaelindra",
            "Aelriel","Aeriel","Afiel","Agiel","Ahiel","Airiel","Akiel",
            "Alriel","Amiel","Aniel","Aoriel","Apriel","Aqiel","Ariel","Asriel","Atriel",
        ],
        "surname": [
            "Brightmantle","Dawnbringer","Dawnfire","Dawnmantle","Dawnguard","Dawnshield",
            "Dawnstar","Dawnsword","Dawnwatch","Dawnwing","Gloryborn","Goldenhalo","Goldenwing",
            "Heavensent","Holyborn","Holyfire","Holysword","Holywing","Lightborn","Lightbringer",
            "Lightfire","Lightmantle","Lightshield","Lightsword","Lightwatch","Lightwing",
            "Luminousborn","Luminousfire","Luminouswing","Moonborn","Moonfire","Moonmantle",
            "Moonshield","Moonsword","Moonwatch","Moonwing","Radiantborn","Radiantfire",
            "Radiantmantle","Radiantshield","Radiantsword","Radiantwatch","Radiantwing",
            "Starborn","Starfire","Starmantle","Starshield","Starsword","Starwatch","Starwing",
            "Sunborn","Sunfire","Sunmantle","Sunshield","Sunsword","Sunwatch","Sunwing",
        ],
    },

    "Tabaxi": {
        "male": [
            "Arrow's End","Ash on the Wind","Black Claw","Broken Stone","Burning Light",
            "Claw Mark","Cold Winter","Crescent Moon","Dark Moon","Dark Shore","Dead Ember",
            "Distant Thunder","Drifting Cloud","Dusk Walker","Ember's Touch","Fading Echo",
            "Far Star","First Frost","Flint's Edge","Frost Bite","Frozen River","Ghost Wind",
            "Glinting Eye","Golden Mane","Hidden Fang","High Peak","Hollow Night","Iron Claw",
            "Iron Path","Last Ember","Late Storm","Light Paw","Long Rain","Lost Shore",
            "Midnight Fur","Moon's Edge","Nightfall Paws","North Wind","Old Ember","Pale Moon",
            "Quick Paw","Rain's End","Red Mane","Ridge Runner","River's Edge","Running Stream",
            "Rust Edge","Sandy Shore","Scattered Stars","Shadow Paw","Shattered Stone",
            "Short Grass","Silent Paw","Silver Claw","Silver Mane","Slanted Light","Slow River",
            "Small Ember","Smoke Trail","Soft Paw","Stone Edge","Stone Mane","Storm's Eye",
            "Swift Paw","Tall Grass","Thin Moon","Thunder's Edge","Twisted Claw","Two Moons",
            "Warm Rain","Wet Stone","Wind Runner","Winter's End","Wolf's Tooth","Worn Stone",
            "Yellow Grass","Amber Eye","Blazing Path","Cinder Track","Coal Streak","Copper Ear",
            "Dark Stripe","Dust Dancer","Embers Trace","Fallen Branch","Far Wanderer",
            "Flicker Step","Frost Ear","Gold Stripe","Grim Stalker","Hidden Track","Iron Ear",
            "Jade Claw","Long Fang","Moon Eye","Narrow Path","Night Runner","Old Fang",
            "Pale Claw","Quiet Paw","Rough Stone","Scarred Mane","Spotted Hide","Still Water",
            "Thorn Paw","Wandering Eye","Yellow Claw","Blazing Eye","Copper Paw","Iron Eye",
        ],
        "female": [
            "Ancient Rain","April Frost","Autumn Leaf","Burning Dawn","Careful Paws",
            "Clear Stream","Crimson Leaf","Crystal Moon","Dark Waters","Distant Rain",
            "Drifting Petal","Dusk Fire","Ember Glow","Evening Star","Fading Light",
            "Falling Leaf","First Rain","Gentle Rain","Golden Dawn","Grey Mist","Hidden Moon",
            "High Cloud","Jade Water","Late Moon","Leaf Dancer","Leaf's Fall","Light Step",
            "Long Shadow","Midnight Bloom","Moon Dancer","Moon's Glow","Morning Dew",
            "Mountain Peak","Night Bloom","Night's Edge","Pale Dawn","Petals on Wind",
            "Quick Step","Rain Dancer","Rippling Water","River Dancer","Sand Dancer",
            "Scattered Petals","Shadow Dancer","Silver Dawn","Silver Rain","Slow Moon",
            "Small Cloud","Soft Rain","Spring Water","Stone Dancer","Storm Dancer",
            "Sun Dancer","Sunlit Path","Twilight Dancer","Two Paws","Warm Breeze",
            "Water Dancer","Water's Edge","Wind Dancer","Winter Bloom","Wisdom's Touch",
            "Amber Petal","Blazing Leaf","Cinder Bloom","Coal Petal","Copper Bloom",
            "Dark Bloom","Dust Petal","Ember Leaf","Fallen Petal","Flicker Bloom",
            "Frost Leaf","Gold Bloom","Grim Bloom","Hidden Leaf","Iron Bloom","Jade Bloom",
            "Jade Petal","Long Whisker","Moon Petal","Narrow Stream","Night Bloom","Old Leaf",
            "Pale Petal","Quiet Dancer","Rough Stream","Scarred Petal","Spotted Leaf","Still Bloom",
            "Thorn Petal","Wandering Cloud","Yellow Leaf","Blazing Petal","Copper Leaf","Iron Petal",
        ],
        "surname": [
            "Bright River","Cold Peak","Dark Jungle","Distant Shore","Ember Mountain",
            "Far Valley","Frozen Lake","Golden Savanna","Grey Peak","Hidden Glade","High Summit",
            "Iron Ridge","Jade Plateau","Long River","Midnight Jungle","Moon Valley",
            "Mountain Heart","Night Forest","Pale Shore","Red Savanna","River Bend","Rock Ridge",
            "Sand Dune","Shadow Glade","Silver Peak","Slow River","Stone Ridge","Storm Peak",
            "Sun Valley","Tall Mountain","Thunder Peak","Twin Peaks","Warm Shore","Wide River",
            "Wind Plain","Winter Peak","Yellow Savanna",
            "Amber Crest","Blazing Summit","Bronze Vale","Copper Crest","Dark Vale",
            "Ember Crest","Fading Glade","Flicker Vale","Gold Crest","Hidden Vale",
            "Iron Vale","Jade Crest","Long Vale","Pale Crest","Stone Vale","Storm Vale",
        ],
    },

    "Kenku": {
        "male": [
            "Bell-ring","Bell-toll","Caw","Chirp","Chitter","Click","Clack","Clatter","Clink",
            "Cloop","Crack","Creak","Crick","Croke","Croon","Crow","Crunch","Drum","Flap",
            "Flitter","Flutter","Hiss","Keen","Klak","Klink","Knock","Krak","Krek","Krick",
            "Krok","Mock","Natter","Patter","Peck","Perch","Plunk","Rattle","Screech","Shriek",
            "Skreech","Slam","Slap","Slither","Squawk","Squeak","Tap","Tchk","Thud","Thump",
            "Tick","Tik","Tink","Tock","Tunk","Tweet","Twitter","Whir","Whisper","Whistle",
            "Whitt","Wik","Wink","Brass-toll","Cart-rattle","Chain-drag","Coin-clink",
            "Door-creak","Gate-clang","Hammer-ring","Iron-ring","Lock-click","Market-call",
            "Rain-tap","Stone-scrape","Wind-rush","Wood-knock","Bell-chime","Blade-ring",
            "Boot-stamp","Crow-call","Drum-beat","Fire-crack","Flint-spark","Fog-horn",
            "Glass-break","Gold-ring","Guard-shout","Hinge-squeak","Horse-neigh","Inn-noise",
            "Knife-scrape","Log-crack","Market-shout","Metal-ring","Mud-splash","Night-owl",
            "Rope-creak","Sail-snap","Ship-groan","Shutter-bang","Sign-swing","Sky-call",
            "Smoke-rise","Snow-hiss","Sparrow-song","Staff-clap","Stone-drop","Storm-crash",
            "Sword-ring","Tower-bell","Wagon-roll","Watch-cry","Water-drip","Wind-howl",
        ],
        "female": [
            "Bell-chime","Bird-call","Brook-babble","Candle-snap","Cat-purr","Cheese-scrape",
            "Child-laugh","Cloth-rustle","Cloud-drift","Coin-drop","Cook-clatter","Crow-caw",
            "Dawn-bell","Distant-drum","Door-bell","Dusk-call","Ember-pop","Fan-flutter",
            "Fire-whisper","Flute-note","Fountain-splash","Glass-chime","Harp-pluck","Hearth-crackle",
            "Honey-drip","Ice-crack","Kettle-whistle","Lace-rustle","Lark-song","Leaf-rustle",
            "Loom-clack","Lute-string","Meadow-breeze","Moon-bell","Morning-bell","Moth-flutter",
            "Night-bell","Owl-hoot","Petal-fall","Quill-scratch","Rain-song","Reed-pipe",
            "River-song","Robin-call","Rose-thorn","Silk-rustle","Silver-bell","Snow-fall",
            "Soft-bell","Song-bell","Spring-bell","Star-bell","Stream-babble","Sunrise-bell",
            "Swan-call","Thread-snap","Tide-bell","Tree-creak","Twilight-bell","Vine-creak",
            "Water-bell","Willow-sway","Wind-bell","Wind-chime","Wing-beat","Winter-bell",
            "Blossom-fall","Bough-sway","Canary-call","Dew-drop","Dove-coo","Fern-sway",
            "Firefly-glow","Fog-drift","Frost-crack","Garden-hum","Gentle-bell","Glade-song",
            "Gossamer-shift","Grove-murmur","Heather-sway","Hollow-toll","Hummingbird-wing",
        ],
        "surname": [
            "Broken Wing","Cracked Beak","Crooked Talon","Dull Feather","Empty Nest",
            "Fallen Feather","Frayed Wing","Grey Feather","Lost Feather","Mended Wing",
            "Mismatched Feather","Muddy Talon","Old Nest","Patched Wing","Ragged Feather",
            "Ragged Wing","Scarred Beak","Scarred Talon","Shadow Wing","Short Feather",
            "Tattered Wing","Torn Feather","Worn Feather","Worn Talon",
            "Bent Talon","Black Feather","Cropped Wing","Dark Nest","Dim Feather",
            "Dusty Feather","Frail Wing","Hollow Nest","Ink Feather","Limping Wing",
            "Mottled Feather","Nicked Beak","Pale Feather","Quiet Feather","Ruffled Wing",
        ],
    },

    # ── New Races ────────────────────────────────────────────────────────────

    "Firbolg": {
        # Celtic/Gaelic-inspired; firbolg rarely share true names, but many adopt them.
        "male": [
            # Gaelic / Celtic names
            "Angus","Bran","Brennan","Caelan","Callum","Cian","Coel","Conall","Cormac",
            "Declan","Diarmuid","Donncha","Eamon","Fearghus","Ferghus","Finnian","Galvyn",
            "Hamish","Iain","Iomhar","Kenneth","Keegan","Lorchan","Lorcan","Magnus",
            "Muirdach","Murdoch","Niall","Oisin","Padraig","Ragnall","Riordan","Ruari",
            "Seamus","Senan","Shane","Tadhg","Terence","Tiernan","Uilleam","Urdnoch",
            "Vorvan","Brom","Cormag","Derval","Gulliver","Ailill","Artach","Brandubh",
            "Cathair","Cathal","Conchobar","Conor","Criomhthann","Cunobelinos",
            "Daire","Donnchadha","Dubhthach","Eochaidh","Eogan","Ercol","Fachtna",
            "Fearadhach","Fearghal","Feidhlim","Fionn","Flann","Flaithbheartach",
            "Garbhan","Gilla","Giollapadraig","Gormlaith","Grainne","Maolmhuire",
        ],
        "female": [
            # Gaelic / Celtic names
            "Aoife","Brigid","Briallen","Caoimhe","Catriona","Daireann","Deirdre",
            "Eibhlin","Etain","Fionnuala","Fionnula","Gormlaith","Grainne","Honoria",
            "Imogen","Iseult","Jorunn","Keelagh","Lasair","Maeve","Meadhbh","Morrigan",
            "Niamh","Nuala","Oonagh","Orlaith","Roisin","Saoirse","Siobhan","Sorcha",
            "Treasa","Una","Ailidh","Barrfind","Bebhinn","Cairenn","Ciannait",
            "Cliodhna","Cobhlaith","Crochnaite","Derbforgaill","Dervla","Doireann",
            "Dubheasa","Eachna","Etaine","Fidelm","Finnguala","Gormfhlaith","Grainach",
            "Lasairfhiona","Liadan","Luthmara","Medb","Moninne","Muireann","Muirenn",
            "Muirgheal","Muiriol","Sadhbh","Saibh","Sailbhe","Scathach","Sioch","Taillte",
        ],
        "surname": [
            "Rootfather","Treestride","Mosscloak","Fernwalker","Streamcaller","Heartwood",
            "Oakmantle","Deepglade","Thornwarden","Wildbloom","Stoneheart","Barkcrown",
            "Mirefoot","Mossheart","Dawnbloom","Cedarfoot","Deeproot","Elmwarden",
            "Fernheart","Forestcrown","Grovewarden","Heathermantle","Ivycloak","Ivywarden",
            "Leafcrown","Leafwarden","Marshfoot","Meadowmantle","Mistcloak","Moorfoot",
            "Pinemantle","Primrosefoot","Rivercrown","Reedcloak","Rootcloak","Sagemantle",
            "Shadeglade","Springfoot","Stonecloak","Streamfoot","Swampwarden","Thicketwarden",
            "Thorncloak","Timberfoot","Tundramantle","Willowcloak","Willowwarden",
        ],
    },

    "Githyanki": {
        # Planar warriors from the Astral Sea; harsh, consonant-heavy names.
        "male": [
            # PHB names
            "Belith","Dak","Irdoc","Meldavh","Nellis","Quith","Smadic","Tlanek","Vur","Xith","Yrlk","Zaer",
            # Additional quality names
            "Aakath","Athar","Erith","Farruk","Girak","Harrak","Ilrath","Jakrak","Kalrak",
            "Larak","Marak","Narak","Orak","Parak","Qurak","Rarak","Sarak","Tarak","Varak",
            "Arrak","Barrak","Darrak","Errak","Farrak","Garrak","Harrak","Irrak","Jarrak",
            "Karrak","Larrak","Marrak","Narrak","Orrak","Parrak","Rarrak","Sarrak","Tarrak",
            "Urrak","Varrak","Warrak","Xarrak","Yarrak","Zarrak","Belrak","Berrak","Birrak",
            "Bolrak","Borrak","Brarak","Brerrak","Brorrak","Brurrak","Bublrak","Buldrak",
            "Chalrak","Chemrak","Chirrak","Cholrak","Chulrak","Clarak","Clerrak","Clorrak",
            "Crarak","Crerrak","Dalkrak","Delmrak","Dilrak","Dolrak","Drarak","Drerak","Drorak",
        ],
        "female": [
            # PHB names
            "Barashk","Elish","Eminak","Ghisnak","Githvari","Immilvara","Reth","Sianor",
            "Sutha","Urak","Vethka","Xane","Yessune","Zara",
            # Additional quality names
            "Arath","Belrath","Celrath","Delrath","Elrath","Firath","Girath","Hirath",
            "Ilrath","Jirath","Kirath","Lirath","Mirath","Nirath","Orirath","Rirath",
            "Sirath","Tirath","Virath","Xirath","Yirath","Zirath","Anath","Banath",
            "Cenath","Denath","Enath","Fanath","Ganath","Hanath","Ianath","Janath",
            "Kanath","Lanath","Manath","Nanath","Oanath","Panath","Ranath","Sanath",
            "Tanath","Uanath","Vanath","Wanath","Xanath","Yanath","Zanath","Belash",
            "Berash","Birash","Bolash","Borash","Brarak","Brerash","Brorash","Brurash",
            "Chalash","Chemash","Chirash","Cholash","Chulash","Clarash","Clerash","Clorash",
        ],
        # Githyanki use military titles; "surname" here represents rank/epithet.
        "surname": [
            "Bladewarden","Mindbreaker","Voidwalker","Psiward","Soulrender","Chainbreaker",
            "Astralborn","Voidborn","Skeinwalker","Starraider","Planebreaker","Kith'rak",
            "Sarth","Gish","of the Rrakkma","Githborn","Mindslayer","Void-touched",
            "Astral-sworn","Silver-sworn","Blademaster","Mindmaster","Voidmaster",
            "Planemaster","Starborn","Astralsworn","Psiblade","Psimind","Psisword",
            "Mindward","Soulward","Voidward","Planeward","Starward","Astralward",
        ],
    },

    "Goliath": {
        # Three-name tradition: birth name, earned nickname, clan name.
        # "male"/"female" are birth names; "surname" is the nickname or clan name.
        "male": [
            # PHB birth names (largely gender-neutral but split here for usability)
            "Aukan","Eglath","Gauthak","Ilikan","Keothi","Kuori","Lo-Kag","Manneo",
            "Maveith","Orilo","Paavu","Pethani","Thotham","Uthal","Vimak",
            # Additional quality names
            "Thorrim","Valgrim","Karog","Turath","Harag","Vorak","Zorak","Borak",
            "Dorak","Gorakh","Harath","Ilgrak","Korakh","Lorath","Morah","Norak",
            "Orakh","Porak","Rorah","Sorak","Torak","Urak","Worah","Yarag","Zarag",
            "Abrak","Adrak","Agrak","Ahrak","Airak","Ajrak","Akrak","Alrak","Amrak",
            "Anrak","Aorak","Aprak","Aqrak","Arrak","Asrak","Atrak","Aurak","Avrak",
            "Awrak","Axrak","Ayrak","Azrak","Bakrak","Balrak","Bamrak","Banrak","Barrak",
            "Basrak","Batrak","Bavrak","Bawrak","Baxrak","Bayrak","Bazrak","Bekrak",
        ],
        "female": [
            # PHB birth names
            "Gae-Al","Nalla","Thalai","Vaunea",
            # Additional quality names
            "Ilkara","Karthana","Lorala","Marvala","Namala","Orvala","Parvala",
            "Rarvala","Sarvala","Tarvala","Ulvala","Varvala","Xarvala","Yarvala","Zarvala",
            "Arala","Barala","Carala","Darala","Erala","Farala","Garala","Harala",
            "Abala","Adala","Agala","Ahala","Aiala","Ajala","Akala","Alala","Amala",
            "Anala","Aoala","Apala","Aqala","Arala","Asala","Atala","Auala","Avala",
            "Awala","Axala","Ayala","Azala","Bakala","Balala","Bamala","Banala","Barala",
            "Basala","Batala","Bavala","Bawala","Baxala","Bayala","Bazala","Bekala",
            "Belala","Berala","Birala","Bolala","Borala","Braala","Breala","Broala",
        ],
        # For Goliath, "surname" doubles as earned nickname or clan name.
        "surname": [
            # Earned nicknames (most common in play)
            "Bearkiller","Cragclimber","Dawncaller","Fearless","Flintfinder","Horncarver",
            "Ironhide","Keeneye","Lonehunter","Longleap","Mountainfoot","Nightglow",
            "Riverrunner","Rockbreaker","Shadowhunter","Steadyhand","Stoneback","Stormvoice",
            "Tidecaller","Twistedlimb","Windspeaker","Wordpainter","Highpeak","Deepcave",
            "Icebreaker","Trailbreaker","Fireholder","Coldrunner","Swiftclimber","Hardenback",
            # Clan names
            "Anakalathai","Elanithino","Gathakanathi","Kalagiano","Katho-Olavi","Kolae-Gileana",
            "Ogolakanu","Thuliaga","Thunukalathi","Vaimei-Laga",
            "Akmenos","Barathos","Catharak","Dagnathos","Egalathos",
        ],
    },

    "Hobgoblin": {
        # Militaristic; names are harsh and efficient. Females serve as warriors too.
        "male": [
            "Hup","Gorak","Malzak","Urgrak","Thrash","Grimnak","Ardrak","Barnak","Balkith",
            "Binlak","Boltrak","Dromak","Dulrak","Fornak","Gralak","Grothak","Gulrak",
            "Halgak","Harnak","Hemrak","Holgak","Hurnak","Kaldrak","Kalgak","Kanthrak",
            "Karnak","Koltrak","Konrak","Kornak","Nardrak","Nornak","Nurgak","Orgrak",
            "Ornak","Rolgak","Ronrak","Targak","Thargak","Thrak","Torgak","Ulnak","Urgak",
            "Urnak","Valgak","Varnak","Vorgak","Warnak","Yornak","Zalgak","Zarnak","Zornak",
            "Ardag","Ardeg","Ardig","Ardog","Ardug","Arnak","Arneg","Arnig","Arnog","Arnug",
            "Baldag","Baldeg","Baldig","Baldog","Baldug","Bardag","Bardeg","Bardig","Bardog",
            "Boldag","Boldeg","Boldig","Boldog","Boldug","Bordag","Bordeg","Bordig","Bordog",
            "Daldag","Daldeg","Daldig","Daldog","Daldug","Dardag","Dardeg","Dardig","Dardog",
            "Doldag","Doldeg","Doldig","Doldog","Doldug","Dordag","Dordeg","Dordig","Dordog",
            "Dromnak","Dromnik","Dromnok","Dromnuk","Dultnak","Dultnik","Dultnok","Dultnuk",
            "Durgak","Durgek","Durgik","Durgok","Durguk","Durgnak","Durgnek","Durgnok",
        ],
        "female": [
            "Bolga","Darkha","Gorsha","Harka","Hursha","Karsha","Kolsha","Korsha","Lagsha",
            "Malgha","Morgha","Narkha","Norsha","Orgsha","Rorsha","Talgha","Tarkha",
            "Thorgha","Torgsha","Ulgha","Urgsha","Vargha","Vorkha","Wargha","Yargha","Zargha",
            "Balksha","Bolsha","Dorkha","Dulgha","Dulsha","Dursha","Galkha","Gargha",
            "Garsha","Gorgha","Gorkha","Gosha","Gralkha","Gronsha","Grulsha","Grudsha",
            "Arsha","Arnsha","Balsha","Barsha","Batsha","Bergsha","Binsha","Birsha",
            "Bolsha","Borsha","Bransha","Brodsha","Buksha","Bursha","Dalsha","Darksha",
            "Darsha","Delsha","Dergsha","Dersha","Dolsha","Dorgsha","Dorsha","Drolsha",
            "Dromsha","Dultsha","Durgsha","Dursha","Falksha","Fargsha","Farsha","Felsha",
            "Fergsha","Fersha","Folsha","Folgsha","Forksha","Forsha","Galsha","Galgsha",
        ],
        "surname": [
            "Ironguard","Bloodcrest","Warfist","Grimspear","Shieldmarch","Redlance",
            "Steelbrow","Ironbrow","Warmark","Grimblade","Bladeguard","Ironmark",
            "Shieldmark","Grimmark","Ironband","Warband","Grimband","Arrowmark",
            "Ashspear","Battlemark","Blademark","Boldbrow","Boldmark","Crimsonspear",
            "Darkspear","Dreadmark","Goreband","Grimsword","Hardmark","Ironspear",
            "Steelmark","Swordband","Warbrow","Warspear","Greyspear","Coldmark",
        ],
    },

    "Lizardfolk": {
        # Simple, hissing sounds; often CVC patterns with sibilants.
        "male": [
            # PHB names
            "Aryte","Driss","Ixas","Orak","Rash","Urak","Zri","Enshaa","Eshin",
            # Additional quality names
            "Lethrix","Sethiss","Xilix","Klarrix","Skarrix","Thriss","Kliss","Karrek",
            "Sarrek","Tarrek","Varrek","Karrix","Sarrix","Tarrix","Varrix",
            "Arshiss","Bashisk","Cressik","Drathiss","Essith","Fressik","Grissath",
            "Hressith","Krashik","Lireth","Marrath","Narriss","Orrath","Prassath",
            "Rassith","Sarrath","Tarrath","Urrith","Varrith","Warriss","Xarrith",
            "Yassith","Zarrith","Kashik","Rissath","Tashik","Vashik","Yassik","Zashik",
            "Slishiss","Glissath","Thrissath","Arrix","Brrix","Crrix","Drrix","Errix",
            "Frrix","Grrix","Hrrix","Irrix","Jrrix","Krrix","Lrrix","Mrrix","Nrrix",
            "Orrax","Prrax","Qrrax","Rrrax","Srrax","Trrax","Urrax","Vrrax","Wrrax",
            "Xrrax","Yrrax","Zrrax","Asrix","Bsrix","Csrix","Dsrix","Esrix","Fsrix",
        ],
        "female": [
            # PHB names
            "Aile","Issara","Karess","Lirex","Lress","Parchess","Rissit","Seshiss","Tiss",
            # Additional quality names
            "Arsha","Ersha","Irsha","Orsha","Ursha","Karsha","Sarsha","Tarsha","Varsha",
            "Bashira","Cassith","Dressith","Elissith","Fessith","Glissith","Hashira",
            "Illissith","Jassith","Kassitha","Lassith","Massith","Nassith","Rassitha",
            "Sassitha","Tassitha","Vassitha","Wassith","Xassith","Yassitha","Zassitha",
            "Arrixxa","Brrixxa","Crrixxa","Drrixxa","Errixxa","Frrixxa","Grrixxa",
            "Hrrixxa","Irrixxa","Jrrixxa","Krrixxa","Lrrixxa","Mrrixxa","Nrrixxa",
            "Orraxxa","Prraxxa","Rraxxa","Srraxxa","Trraxxa","Urraxxa","Vrraxxa",
            "Wrraxxa","Xrraxxa","Yrraxxa","Zrraxxa","Asrixxa","Bsrixxa","Csrixxa",
            "Dsrixxa","Esrixxa","Fsrixxa","Gsrixxa","Hsrixxa","Isrixxa","Jsrixxa",
        ],
        "surname": [
            "Muddepth","Scaleclaw","Reedsong","Riverwade","Marshblood","Swampborn",
            "Wetstone","Bogwatcher","Mudscale","Deepwater","Stillwater","Rushwater",
            "Poolwatcher","Dankmarsh","Coldwater","Darkwater","Deepmarsh","Dimwater",
            "Dullscale","Fangsong","Flatwater","Freshwater","Graywater","Greenwater",
            "Hisswater","Ironscale","Jadescale","Longscale","Mudsong","Murkwater",
            "Pondwatcher","Reedscale","Ripplewater","Rockwater","Roughwater","Silentwater",
            "Siltwater","Slimewater","Slowwater","Softscale","Stickywater","Stonescale",
        ],
    },

    "Warforged": {
        # Constructs; typically genderless but may identify with a gender.
        # Names are functional, descriptive, or taken from other cultures.
        "male": [
            "Ajax","Andros","Armand","Arthur","Bastion","Brazen","Bridge","Bulwark",
            "Cauldron","Charter","Cobalt","Crane","Crankshaft","Dagger","Dauntless",
            "Defender","Designate","Envoy","Fender","Flint","Forge","Fortress","Fulcrum",
            "Gadget","Gauge","Gauntlet","Gear","Govern","Guardian","Hammerhead","Herald",
            "Honored","Ironside","Judgment","Keystone","Lancer","Lantern","Ledger",
            "Legion","Linkage","Machete","Mantle","Marshal","Maul","Mender","Monument",
            "Morale","Muster","Obelisk","Order","Paragon","Patrol","Phalanx","Pillar",
            "Protocol","Rampart","Ranger","Reckoner","Rectitude","Redoubt","Regent",
            "Reliant","Sentinel","Signal","Solder","Spanner","Stalwart","Standard",
            "Steadfast","Steward","Stronghold","Tactician","Templar","Threshold","Torque",
            "Trident","Triton","Trophy","Turret","Valor","Vanguard","Vector","Vigilant",
        ],
        "female": [
            "Alight","Artisan","Aspect","Beacon","Blessing","Brooch","Candle","Canvas",
            "Carve","Catalyst","Chalice","Cipher","Clarity","Codex","Compass","Craft",
            "Cradle","Crystal","Dawnfire","Devotion","Diamond","Dusk","Echo","Enigma",
            "Etch","Faithful","Fervor","Filament","Foresight","Fortune","Fracture","Gild",
            "Gleam","Grace","Hallow","Harmony","Hope","Imbue","Inspire","Kindle","Lantern",
            "Lumen","Mandate","Mercy","Mirror","Morrow","Oracle","Pattern","Pilgrim",
            "Prism","Promise","Radiance","Reason","Reliquary","Resolve","Reverence","Ritual",
            "Rune","Sanctum","Serenity","Silence","Silver","Solace","Spirit","Sterling",
            "Synthesis","Tempest","Trace","Truth","Unity","Valor","Virtue","Vision",
            "Wisdom","Wonder","Zenith","Zephyr","Axiom","Balance","Clarity","Dawnlight",
        ],
        "surname": [
            # Designation-style surnames / unit designations
            "Mark-I","Mark-II","Mark-III","Mark-IV","Mark-VII","Mark-XII",
            "Seven","Three","Five","Eleven","Seventeen","Twenty-Three",
            "Forge-Seven","First-Mark","Battleborn","Warborn","Peacekeeper",
            "Vanguard","Sentinel","Warden","First-Light","Ironborn","Steelborn",
            "Coldforge","Ironforge","Silverforge","Goldforge","Darkforge",
            "Unit-One","Unit-Seven","Unit-Twelve","Unit-Fifteen","Unit-Omega",
            "Prototype","Second-Cast","Third-Cast","Final-Cast","Trial-Cast",
        ],
    },
}
