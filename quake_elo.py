class QuakeEloManager:
    
    def __init__(self, db, db_key, handicap_factor, k_factor, default_rating=100.):
        self.db = db
        self.db_key = db_key
        self.handicap_factor = handicap_factor
        self.k_factor = k_factor
        self.default_rating = default_rating
 
    def _db_get(self, key, default=None):
        key = self.db_key + key
        return self.db.get(key) or default
        
    def _db_set(self, key, value):
        key = self.db_key + key
        self.db.set(key, value)

    def get_player_merit(self, steam_id):
        steam_id = str(steam_id)
        result = float(self._db_get('player:' + steam_id, self.default_rating))
        assert result > 0
        return result

    def set_player_merit(self, steam_id, merit):
        return self._db_set('player:' + steam_id, merit)

    def sids_to_handicaps(self, sids):
        sid_to_merit = dict( (sid, self.get_player_merit(sid)) for sid in sids )
        sid_to_handicap = self.sid_to_merit_to_handicap(sid_to_merit)
        to_return = [sid_to_handicap[sid] for sid in sids]
        return to_return

    def sid_to_merit_to_handicap(self, sid_to_merit):
        sids = sid_to_merit.keys()

        count = len(sids)

        if count == 0:
            return []
        elif count == 1:
            return [100.]

        in_ascending_merit = sorted(sids, key = lambda sid: sid_to_merit[sid])
        base_merit = sid_to_merit[in_ascending_merit[0]]

        sid_to_handicap = {in_ascending_merit[0]: 100.}
        for sid in in_ascending_merit[1:]:
            merit = sid_to_merit[sid]
            assert merit >= base_merit
            perc_needed_to_reduce = 1. - base_merit / merit
            handicap = 100. / (((merit/base_merit) - 1) / self.handicap_factor + 1)
            assert handicap > 0
            if handicap > 100.:
                handicap = 100.
            sid_to_handicap[sid] = handicap

        return sid_to_handicap

    def update(self, results):
        """
        "results" is a list of dicts with the following structure:
        [
            {
                "steam_id": ...,
                "score": ...,
                "time": ...,
                "handicap": ...,
            }
            ...
        ]
        """

        if not results:
            return

        results = [
            {
                'steam_id': d['steam_id'],
                'score': float(d['score']) if int(d['score']) >= 0 else 0,
                'time': float(d['time']), # milliseconds
                'handicap': float(d['handicap']),
            }
            for d in results
            if int(d['time']) > 0 and int(d['handicap']) > 0
        ]

        max_time = max(float(d['time']) for d in results)
        max_handicap = max(float(d['handicap']) for d in results)
        sum_score = sum(float(d['score']) for d in results)

        if sum_score == 0:
            return

        effective_results = []
        for d in results:
            effective_dict = {
                'steam_id': d['steam_id'],
                'score': (
                    d['score'] 
                    * (float(max_time) / d['time'])
                    * (1 + ( (max_handicap / d['handicap'] - 1) * self.handicap_factor))
                ),
                'merit': self.get_player_merit(d['steam_id']),
            }
            effective_results.append(effective_dict)

        del results

        sum_score = sum(float(d['score']) for d in effective_results)
        sum_merits = sum(d['merit'] for d in effective_results)

        assert sum_score > 0
        assert sum_merits > 0

        for d in effective_results:
            d['perc_score'] = d['score'] / sum_score
            d['expected_score'] = d['merit'] / sum_merits
            d['ratio'] = d['perc_score'] / d['expected_score']

        for d in effective_results:
            d['adjusted_ratio'] = 1 + ((d['ratio']-1) * self.k_factor)

        print(effective_results)

        for d in effective_results:
            self.set_player_merit(
                d['steam_id'],
                d['merit'] * d['adjusted_ratio'],
            )

