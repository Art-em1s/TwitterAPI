from TwitterAPI import TwitterAPI, TwitterOAuth, TwitterRequestError, TwitterConnectionError, TwitterPager
import json

CONVERSATION_ID = '1318769013640450048'

class Node:
	def __init__(self, data):
		"""data is a tweet's json object"""
		self.data = data
		self.children = []

	def id(self):
		"""a node is identified by its author"""
		return self.data['author_id']

	def reply_to(self):
		"""the reply-to user is the parent of the node"""
		return self.data['in_reply_to_user_id']

	def print_tree(self, level):
		"""level is 0 for the root node, then incremented for every generation"""
		print(f'{level*"_"}{level}: {self.id()}')
		level += 1
		for child in self.children:
			child.print_tree(level)

	def find_parent_of(self, node):
		"""append a node to the children of it's reply-to user"""
		if node.reply_to() == self.id():
			self.children.append(node)
			return True
		for child in self.children:
			if child.find_parent_of(node):
				return True
		return False

try:
	o = TwitterOAuth.read_file()
	api = TwitterAPI(o.consumer_key, o.consumer_secret, auth_type='oAuth2', api_version='2')

	# GET ROOT OF THE CONVERSATION

	r = api.request(f'tweets/:{CONVERSATION_ID}',
		{
			'tweet.fields':'author_id,conversation_id,created_at,in_reply_to_user_id'
		})

	for item in r:
		root = Node(item)
		print(f'ROOT {root.id()}')

	# GET ALL REPLIES IN CONVERSATION
	# (RETURNED IN REVERSE CHRONOLOGICAL ORDER)

	pager = TwitterPager(api, 'tweets/search/recent', 
		{
			'query':f'conversation_id:{CONVERSATION_ID}',
			'tweet.fields':'author_id,conversation_id,created_at,in_reply_to_user_id'
		})

	# "wait=2" means wait 2 seconds between each request.
	# The rate limit is 450 requests per 15 minutes, or
	# 15*60/450 = 2 seconds. 

	orphans = []

	for item in pager.get_iterator(wait=2):
		node = Node(item)
		print(f'{node.id()} => {node.reply_to()}')
		# REMOVE ORPHANS THAT ARE CHILDREN OF THE NODE
		orphans = [orphan for orphan in orphans if not node.find_parent_of(orphan)]
		# IF NODE CANNOT BE PLACED IN CURRENT TREE, ADD NODE TO ORPHANS
		if not root.find_parent_of(node):
			orphans.append(node)

	print('\nTREE...')
	root.print_tree(0)
	assert len(orphans) == 0, f'{len(orphans)} orphaned tweets'

except TwitterRequestError as e:
	print(e.status_code)
	for msg in iter(e):
		print(msg)

except TwitterConnectionError as e:
	print(e)

except Exception as e:
	print(e)