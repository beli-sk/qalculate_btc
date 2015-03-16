#!/usr/bin/env python3
#
# BTC updater for Qalculate
#
# Copyright 2015 Michal Belica <devel@beli.sk>
#
# This file is part of iphttp.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import argparse
from urllib import request
from decimal import Decimal

from lxml import etree

# Select unit in category currency of type alias with name BTC, tied to EUR
SELECTION_XPATH = "/QALCULATE/category[title='Currency']/unit[@type='alias'][title='Bitcoin'][base/unit='EUR']"
# defaults
UNITS_FILE = '~/.qalculate/definitions/units.xml'
EXCHANGE_URL_LAST = "https://api.bitcoinaverage.com/ticker/EUR/last"
EXCHANGE_URL_AVG = "https://api.bitcoinaverage.com/ticker/EUR/24h_avg"

def create_tree():
    root = etree.Element('QALCULATE')
    return etree.ElementTree(root)

def create_unit():
    unit = etree.Element('unit', type='alias')
    etree.SubElement(unit, 'title').text = 'Bitcoin'
    etree.SubElement(unit, 'names').text = 'BTC,XBT'
    base = etree.SubElement(unit, 'base')
    etree.SubElement(base, 'unit').text = 'EUR'
    etree.SubElement(base, 'relation')
    etree.SubElement(base, 'exponent').text = '1'
    return unit

def output(tree):
    # create string text output from XML etree
    return etree.tostring(tree, xml_declaration=True, encoding='UTF-8').decode('utf-8')

def main(units_file, url, verbose):
    try:
        with open(units_file, 'r') as f:
           tree = etree.parse(f)
    except FileNotFoundError:
        tree = create_tree()
    root = tree.getroot()
    
    units = root.xpath(SELECTION_XPATH)
    if not units:
        if verbose:
            print("No unit matches selection, will create one.")
        unit = create_unit()
        # append it into Currency category
        currencies = root.xpath("/QALCULATE/category[title='Currency']")
        if not currencies:
            # create the category
            currency = etree.SubElement(root, 'category')
            etree.SubElement(currency, 'title').text = 'Currency'
        elif len(currencies) > 1:
            raise Exception('There are multiple Currency categories.')
        else:
            currency = currencies[0]
        currency.append(unit)
    elif len(units) > 1:
        raise Exception("More than one matching units found.")
    else:
        unit = units[0]
    
    # load exchange rate
    if verbose:
        print('Loading EUR/BTC rate from {}'.format(url))
    response = request.urlopen(EXCHANGE_URL_LAST)
    rate = Decimal(response.read().decode('utf-8'))
    relation = unit.xpath('//base/relation')[0]
    relation.text = str(rate)
    
    # write output back to file
    outputdata = output(tree)
    with open(units_file, 'w') as f:
        f.write(outputdata)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Update BTC rate in Qalculate from bitcoinaverage.com')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--last', '-l', action='store_true', default=False,
            help='Use last trade instead of 24h average value.')
    group.add_argument('--url', '-u', default=None,
            help='Custom URL which returns EUR/BTC rate in plain text.')
    parser.add_argument('--file', '-f', default=UNITS_FILE,
            help='Qalculate units definition file (default: %(default)s).')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
            help='Verbose output.')
    args = parser.parse_args()

    if args.url:
        url = args.url
    else:
        url = EXCHANGE_URL_LAST if args.last else EXCHANGE_URL_AVG

    main(os.path.expanduser(args.file), url, args.verbose)
    
