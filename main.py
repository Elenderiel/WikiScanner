import asyncio
import aiohttp
import json
import argparse

import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network

parser = argparse.ArgumentParser()
parser.add_argument('pageName', type=str, help='Name of the Wikipedia site you want to scan')
parser.add_argument('-d', '--depth', type=int, help='set the maximum depth of the recursive search (default: 3)')
parser.add_argument('-l', '--links', type=int, help='set the maximum number of links, that are considered per article (default: 10)')
args = parser.parse_args()

url = 'https://en.wikipedia.org/w/api.php'
title = 'Python_(programming_language)'
maxDepth = 3
maxLinks = 10
if args.depth: maxDepth = args.depth
if args.links: maxLinks = args.links
if args.pageName: title = args.pageName 

parameter = {
    'action'  : 'parse',
    'format' : 'json', 
    'page' : '', 
    'prop' : 'links',
}

async def fetchData(title, session):
    parameter['page'] = title
    try:
        response = await session.get(url=url, params=parameter)
        if response.status == 200:
            return await response.json()
        else: print(f'unable to fetch data from {title}: {response.status}')
    except Exception as e:
        print(f'An error occured while fetching links from: {title}', e)

#creates async tasks to fetch child links (fetchData) for all links
async def getChildNodes(titles: list):
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(fetchData(title, session)) for title in titles]
            result = await asyncio.gather(*tasks)
            return result
    except Exception as e:
        print('An error occured while creating async tasks: ', e)

#fetches the all child links, adds them as nodes to the graph, Recursion for all child links until depth limit is met
def recursiveGraphBuild(Nodes, depth = 1):
    print(f'Depth: {depth}')
    links, linksFetched = [], 0
    try:
        #extracts links from each response.json object in async return list
        for i, resultObject in enumerate(asyncio.run(getChildNodes(Nodes))):
            if 'parse' in resultObject and 'links' in resultObject['parse']: 
                childNodes = [link['*'] for link in resultObject['parse']['links'] if link['ns'] == 0]
                linksFetched += len(childNodes)
                linkDict[Nodes[i]] = linkDict.get(Nodes[i], 0) + len(childNodes)
                childNodes = childNodes[:maxLinks]
            else:
                print("response doesn't contain links object: ", Nodes[i])
            links += childNodes
            #adds the fetched links to the parent node (creates parent node if it doesn't exist)
            graph[Nodes[i]] = graph.get(Nodes[i], []) + childNodes
    except Exception as e:
        print('unable to construct graph: ', e)

    print(f'links fetched at depth {depth}: {linksFetched} \n ...')
    if depth < maxDepth:
        recursiveGraphBuild(links, depth + 1)

graph = {}
linkDict = {}
recursiveGraphBuild([title])

G = nx.Graph(graph)
Graph = Network(height='100vh', width='100%', bgcolor='#11111b', font_color='white')
Graph.barnes_hut(spring_length=30, gravity=-40000, spring_strength=0.02)
Graph.from_nx(G)
for node in Graph.nodes:
    if node['id'] == title: node['color'] = 'red'
    #node['value'] = len(Graph.get_adj_list()[node['id']])
    if node['id'] in linkDict.keys():
        node['value'] = linkDict[node['id']]
        node['title'] = str(node['value'])
Graph.show_buttons(filter_=['physics'])
Graph.show('test.html', notebook=False)