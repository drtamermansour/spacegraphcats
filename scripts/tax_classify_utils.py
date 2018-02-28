import collections
from sourmash_lib.lca import lca_utils

taxonomy_levels = ['superkingdom', 'phylum', 'class', 'order', 'family',
                   'genus', 'species', 'strain']


def summarize_taxonomic_purity(minhash_collections, lca_db, verbose=False):
    total = 0
    n_empty = 0
    pure_at_rank = collections.defaultdict(int)

    # for each group,
    for g in minhash_collections:
        total += 1

        # collect all the hash values for this minhash collection
        mins = g.get_mins()

        # now, collate the lineage assignments across all the hashes
        assignments = collections.Counter()
        for m in mins:
            x = lca_db.get_lineage_assignments(m)
            for lineage in x:
                assignments[lineage] += 1

        if not assignments:
            # empty, no hash assignments for this group!
            n_empty += 1
            continue

        # for each taxonomic level, calculate purity
        for level, rank in enumerate(reversed(taxonomy_levels)):
            index = len(taxonomy_levels) - level

            # track number of different items at this tax rank
            level_counter = collections.Counter()

            count = 0
            for lineage, count in assignments.items():
                # trim the lineage back to the given rank
                sublineage = lineage[:index]
                assert sublineage[-1].rank == rank, lineage

                # count the trimmed lineage!
                level_counter[sublineage] += count

            ### Note for @sgsmob: at this point, 'level_counter' contains
            ### all lineages trimmed back to 'rank', with associated counts.
            ### This is a collections.Counter object, so both .items() and
            ### the method '.most_common()' will return lists of
            ### (lineage, count), with 'most_common()' returning them in
            ### highest-to-lowest order.

            ### Here is some code to compute the fraction of the bin that
            ### belongs to the top-ranked lineage:

            top_lineage, top_count = next(iter(level_counter.most_common()))
            total_hashes = sum(level_counter.values())
            lineage_display = "; ".join(lca_utils.zip_lineage(top_lineage))
            if verbose:
                print(rank, '{:.1f}%'.format(top_count / total_hashes * 100), lineage_display)

            if len(level_counter) == 0:   # should never get here!
                assert 0, assignments

            # if we have a 100% pure bin, quit now.
            if top_count / total_hashes == 1.0:
                pure_at_rank[rank] += 1

                # print out the egregiously bad ones just to double check...
                if rank in ('phylum', 'superkingdom') and verbose:
                    print('---')
                    for assignment in assignments:
                        print('\t', '; '.join(lca_utils.zip_lineage(assignment)))
                break

    # calculate summary numbers!
    print('total bins: {}'.format(total))
    print('unassigned bins: {}'.format(n_empty))

    sum_pure = 0
    for rank in reversed(taxonomy_levels):
        print('pure at rank {}: {}'.format(rank, pure_at_rank[rank]))
        sum_pure += pure_at_rank[rank]

    print('not pure at any rank:', total - sum_pure - n_empty)
