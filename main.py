from sqlalchemy import null
from scrapers.mangasee import MangaseeCrawlerFactory
from scrapers.asuratoon import AsuratoonCrawlerFactory
from scrapers.manhuaplus import ManhuaplusCrawlerFactory
from scrapers.mangareader import MangareaderCrawlerFactory
from utils import crawler_util
from sources.manga_sources import MangaSourceWriter


def create_and_run_crawler(factory):
    crawler = factory.create_crawler()
    crawler.crawl()


if __name__ == "__main__":
    original_ids = ["After-Reincarnation-My-Party-Was-Full-Of-Traps-But-Im-Not-A-Shotacon", "Class-Teni-de-Ore-dake-Haburaretara-Doukyuu-Harem-Tsukuru-Koto-ni-Shita", "Demoted-to-a-Teacher-the-Strongest-Sage-Raises-an-Unbeatable-Class", "Do-You-Think-Someone-Like-You-Could-Defeat-the-Demon-Lord", "Eiyu-Oh-Bu-wo-Kiwameru-Tame-Tensei-Su-Soshite-Sekai-Saikyou-no-Minarai-Kisi", "Endo-and-Kobayashis-Live-Commentary-on-the-Villainess", "Even-Dogs-Go-to-Other-Worlds-Life-in-Another-World-with-My-Beloved-Hound", "Hazure-Skill-Kage-ga-Usui-o-Motsu-Guild-Shokuin-ga", "I-Dont-Really-Get-It-but-It-Looks-Like-I-Was-Reincarnated-in-Another-World", "I-Reincarnated-as-the-Little-Sister-of-a-Death-Game", "I-went-from-the-strongest-job-Dragon-Knight-to-a-beginner-level-job-Carrier", "Inkya-Datta-Ore-no-Seishun-Revenge-Tenshi-sugiru-Ano-Ko-wa-Ayumu-Re-Life", "Isekai-Craft-Gurashi-Jiyu-Kimamana-Seisan-Shoku-No-Honobono-Slow-Life", "Kasouba-No-Nai-Machi-Ni-Kane-Ga-Naru-Toki", "Kizoku-Tensei-Megumareta-Umare-kara-Saikyou-no-Chikara-wo-Eru", "Koko-wa-Ore-ni-Makasete-Saki-ni-Ike-to-Itte-kara-10-Nen-ga-Tattara-Densetsu-ni-Natteita", "Kousha-No-Ura-Ni-Wa-Tenshi-Ga-Umerarete-Iru", "Miss-Miyazen-Would-Love-to-Get-Closer-to-You",
                    "My-Brain-is-Different-Stories-of-ADHD-and-Other-Developmental-Disorders", "Naruto-Sasukes-Story-The-Uchiha-and-the-Heavenly-Stardust-The-Manga", "Nido-Tensei-Shita-Shounen-wa-S-Rank-Boukensha-Toshite-Heion", "Oda-Nobunaga-to-Iu-Nazo-no-Shokugyo-ga-Mahou-Kenshi-yori-Cheat-Dattanode", "Okiraku-Ryoushu-no-Tanoshii-Ryouchi-Bouei", "Senmetsumadou-no-Saikyou-Kenja-Musai-no-Kenja-Madou-wo-Kiwame-Saikyou-e-Itaru", "Shinigami-ni-Sodaterareta-Shoujo-wa-Shikkoku-no-Tsurugi-wo-Mune-ni-Idaku", "Souzou-Renkinjutsushi-wa-Jiyuu-wo-Ouka-suru", "SSS-Rank-Dungeon-de-Knife-Ichihon-Tewatasare-Tsuihou-Sareta-Hakuma-Doushi", "Tanbo-de-Hirotta-Onna-Kishi-Inaka-de-Ore-no-Yome-da-to-Omowareteiru", "Tekito-na-Maid-no-Oneesan-Erasou-de-Ichizu-na-Botchan", "The-Comeback-of-the-Demon-King-Who-Formed-a-Demons-Guild-After-Being-Vanquished-by-the-Hero", "The-Executed-Sage-Is-Reincarnated-as-a-Lich-and-Starts-an-All-Out-War", "The-Hero-Wants-a-Married-Woman-as-a-Reward", "The-White-Mage-Who-Was-Banished-from-the-Heros-Party", "Uketsukejo-ni-Kokuhaku-Shitakute-Guild-ni-Kayoitsumetara-Eiyu-ni-Natteta", "Until-the-Tall-Kouhai-Girl-and-the-Short-Senpai-Boy-Develop-a-Romance", "Yuusha-no-Kawari-ni-Maou-Toubatsu-Shitara-Tegara-o-Yokodoroi-Saremashita"]
    # asuratoon = AsuratoonCrawlerFactory().create_crawler().push_to_db(type='all')
    mangasee = MangaseeCrawlerFactory().create_crawler().crawl(original_ids=original_ids)
    # manhuaplus = ManhuaplusCrawlerFactory().create_crawler().crawl()
    # mangareader = MangareaderCrawlerFactory().create_crawler().push_to_db()
    # print(list_original_ids)
