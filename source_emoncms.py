#!/usr/bin/env python
#-*- coding:utf-8 -*-
import sys

from datetime import datetime
import time
import requests

import pandas as pd
import matplotlib.pyplot as plt

class EmoncmsSource(object):
    """ Get data from emoncms API
    """

    def __init__(self, url):
        self.url = url

    def _get_json(self, url, params=None):
        results = requests.get(url, params=params)
        # error if not 200 for HTTP status
        results.raise_for_status()
        if results.text == "false":
            raise RuntimeError("Impossible to get the data (%s)" % results.url)
        #print query
        return results.json()

    def feeds(self):
        """ Get data about all available feeds
        """
        res = self._get_json(self.url + "/feed/list.json?userid=1")  #XXX: userid=1 to get public data (to check)
        for feed in res:
            feed["date"] = datetime.fromtimestamp(feed["time"])
        return res

    def get_data(self, fid, start_date, delta_sec, nb_data=10000):
        """
        :param fid: feed ID to get
        """
        ## make the requests
        t_start = time.mktime( start_date.timetuple() )*1000
        
        data_brut = []
        nb_read = 0
        nb_each_request = 800
        while nb_read < nb_data:
            # choix du pas de temps
            nb_to_read = min(nb_each_request, nb_data-nb_read)
            t_end = t_start + nb_to_read*delta_sec*1000
            #rint  int( t_start ), int( t_end )
            query = self.url + "/feed/average.json"
            params = {}
            params["id"] = fid
            params["start"] = int(t_start)
            params["end"] = t_end
            params["interval"] = delta_sec
            
            data_brut += self._get_json(query, params)
            nb_read += nb_to_read
            t_start = data_brut[-1][0]
        
        ## convert it to panda
        dates, vals = zip(*data_brut)
        dates = [datetime.fromtimestamp(date/1000) for date in dates]
        ts = pd.Series(vals, index=dates)
        return ts

def main():
    import argparse
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-u", "--url", action='store', type=str, help="emoncms root url")
    parser.add_argument("-f", "--feed_id", action='store', type=int, help="Feed ID")

    args = parser.parse_args()

    # Build emoncms data source object
    emon_src = EmoncmsSource(args.url)

    ## list all feed
    from pprint import pprint
    print("#"*5 + " ALL FEEDS  " + "#"*5)
    feeds = emon_src.feeds()
    for feed in feeds:
        print("* id:{id:<3} name:{name:<16} value:{value:<10} last update:{date}".format(**feed))

    ## Plot one feed
    if args.feed_id:
        print("#"*5 + " PLOT  " + "#"*5)
        start_date = datetime.datetime(2014, 9, 10)
        delta_sec = 60*5
        ts = emon_src.get_data(args.feed_id, start_date, delta_sec, nb_data=10000)
        ts.plot()
        plt.show()

    return 0

if __name__ == '__main__':
    sys.exit(main())


