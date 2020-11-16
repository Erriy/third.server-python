#!/usr/bin/env python3
# -*- coding=utf-8 -*-


class adapter():
    def fp_relationship_create(self, from_fp, to_fp, relationship, timestamp, seed):
        pass

    def fp_relationship_delete(self, from_fp, to_fp, relationship):
        pass

    def fp_relationship_list(self, fp, relationship, page, page_size):
        pass

    def seed_create(self, fp, seeds):
        pass

    def seed_search(self, fp, zone, page, page_size, sort, ending, linked_with):
        pass

    def seed_publish(self, fp, seedid):
        pass

    def seed_info(self, fp, zone, seedid):
        pass

    def seed_history(self, fp, zone, seedid, page, page_size):
        pass

    def seed_delete(self, fp, seedid, all):
        pass

    def seed_block(self, fp, seedid):
        pass

    def seed_unblock(self, fp, seedid):
        pass

    def seed_block_list(self, fp, page, page_size):
        pass

