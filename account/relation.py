from enum import Enum


class RelationStatus(Enum):
	FRIENDS = -1
	USER1_TO_USER2 = 0
	USER2_TO_USER1 = 1
	MUTUAL_FRIEND = 10
	NOT_FRIENDS = -10
