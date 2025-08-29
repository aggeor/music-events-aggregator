import asyncio

from crawler.athinorama import crawl_athinorama
from crawler.iereies_tis_nychtas import crawl_iereies
from crawler.aptaliko import crawl_aptaliko
from crawler.clubber import crawl_clubber
from crawler.more_com import crawl_more_com
from crawler.ticketmaster import crawl_ticketmaster
from database.crud import save_events_to_db
from utils.helper import print_serialized

async def main():
    iereies_data = await crawl_iereies()
    if iereies_data:
        print_serialized(iereies_data)
        await save_events_to_db(iereies_data)
    aptaliko_data = await crawl_aptaliko()
    if aptaliko_data:
        print_serialized(aptaliko_data)
        await save_events_to_db(aptaliko_data)
    athinorama_data = await crawl_athinorama()
    if athinorama_data:
        print_serialized(athinorama_data)
        await save_events_to_db(athinorama_data)
    clubber_data = await crawl_clubber()
    if clubber_data:
        print_serialized(clubber_data)
        await save_events_to_db(clubber_data)
    more_com_data = await crawl_more_com()
    if more_com_data:
        print_serialized(more_com_data)
        await save_events_to_db(more_com_data)
    ticketmaster_data = await crawl_ticketmaster()
    if ticketmaster_data:
        print_serialized(ticketmaster_data)
        await save_events_to_db(ticketmaster_data)

if __name__ == "__main__":
    asyncio.run(main())