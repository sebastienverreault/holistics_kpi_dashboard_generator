#!/usr/bin/env python3

import sys

import numpy as np
import pandas as pd

import locale

from sys import stderr
from os import environ
from string import Template

#
# <file_name>.csv
#
# <kpi_name>,   <kpi_value>
# "My KPI Name", 3.14
#

current_locale = locale.setlocale( locale.LC_ALL, 'en_CA.UTF-8' )

HOLISTICS_DATASET = environ.get('HOLISTICS_DATASET')
HOLISTICS_TABLE = environ.get('HOLISTICS_TABLE')
HOLISTICS_MODEL = environ.get('HOLISTICS_MODEL')

PAGE_WIDTH = 1200
PADDING_WIDTH = 20
NUMBER_BLOCK_WIDE = 3
TITLE_HEIGHT = 120
TITLE_C_OFFSET = (2 * PADDING_WIDTH) + TITLE_HEIGHT
BLOCK_Y_START = PADDING_WIDTH + TITLE_HEIGHT + PADDING_WIDTH
BLOCK_WIDTH_TO_HEIGHT_RATIO = 1.6
BLOCK_WIDTH = round(((PAGE_WIDTH - 2 * PADDING_WIDTH) / NUMBER_BLOCK_WIDE) - ((NUMBER_BLOCK_WIDE - 1) * PADDING_WIDTH), -1)
BLOCK_HEIGHT = round(BLOCK_WIDTH / BLOCK_WIDTH_TO_HEIGHT_RATIO, -1)
BLOCK_PADDING_WIDTH = ((PAGE_WIDTH - 2 * PADDING_WIDTH) - (NUMBER_BLOCK_WIDE * BLOCK_WIDTH)) / (NUMBER_BLOCK_WIDE - 1)

NUMBER_PERCENT_FORMAT_PATTERN = '#,###\\%'
NUMBER_BTC_FORMAT_PATTERN = '#,###0.0000'
NUMBER_USD_FORMAT_PATTERN = '[$$]#,###,,"M"'
NUMBER_DEFAULT_FORMAT_PATTERN = '#,###'

class HolisticsKpiDashboardGenerator:
    def __init__(self, filename):
        try:
            self.kpis_df = pd.read_csv(filename, sep=",", header=0)
            self.filter_field = self.kpis_df.columns[0]
            self.field_field = self.kpis_df.columns[1]
            self.title_underscored = filename.replace('.csv', '')
            self.title = self.title_underscored.replace('_', ' ').title()
            self.description = f"{self.title} Portfolio KPIs"
            self.blocks = []
            self.blocks_position = []
            self.views = []

        except Exception as e:
            print(f"Could not open file '{filename}'")
            print(f"Exception: {e}")

    def generate_dashboard(self):
        try:
            #########
            # blocks
            #########
            for row in self.kpis_df.itertuples():
                block_number = row.Index
                if "(%)" in row[1]:
                    field_format_pattern = NUMBER_PERCENT_FORMAT_PATTERN
                elif "(BTC)" in row[1]:
                    field_format_pattern = NUMBER_BTC_FORMAT_PATTERN
                elif "(USD)" in row[1]:
                    field_format_pattern = NUMBER_USD_FORMAT_PATTERN
                else:
                    field_format_pattern = NUMBER_DEFAULT_FORMAT_PATTERN
                block = self.__block_template(
                    block_number = block_number,
                    block_label = row[1],
                    dataset = HOLISTICS_DATASET,
                    filter_field = self.filter_field,
                    filter_model = HOLISTICS_MODEL,
                    filter_operator = 'is',
                    filter_value = row[1],
                    field_label = row[1],
                    field_model = HOLISTICS_MODEL,
                    field_field = self.field_field,
                    field_aggregation = 'max',
                    field_format_type = 'number',
                    field_format_pattern = field_format_pattern,
                    field_format_group_separator = ',',
                    field_format_decimal_separator = '.',
                )
                self.blocks.append(block)
                x = round((block_number % NUMBER_BLOCK_WIDE) * (BLOCK_WIDTH + BLOCK_PADDING_WIDTH) + PADDING_WIDTH)
                y = round(BLOCK_Y_START + (block_number // NUMBER_BLOCK_WIDE) * (BLOCK_HEIGHT + PADDING_WIDTH))
                w = round(BLOCK_WIDTH)
                h = round(BLOCK_HEIGHT)
                self.blocks_position.append(f"    block v{block_number} {{ position: pos({x}, {y}, {w}, {h}) }}")
            #######
            # view
            #######
            view_number = 1
            label = f"View {view_number}"
            height = round(TITLE_C_OFFSET + (len(self.blocks_position) // NUMBER_BLOCK_WIDE + 1) * (BLOCK_HEIGHT + PADDING_WIDTH))
            grid_size = PADDING_WIDTH
            x = PADDING_WIDTH
            y = PADDING_WIDTH
            w = (PAGE_WIDTH - 2 * PADDING_WIDTH)
            h = TITLE_HEIGHT
            block_title_position = f"block title {{ position: pos({x}, {y}, {w}, {h}) }}"
            view = self.__view_template(
                view_number,
                label,
                height,
                grid_size,
                block_title_position,
                self.blocks_position
            )
            self.views.append(view)
            #######
            # page
            #######
            page_template_name, page = self.__page_template(
                self.title,
                self.title_underscored,
                self.description,
                self.blocks,
                self.views,
            )
            with open(f"{self.title_underscored}.{page_template_name}", 'w') as f:
                f.write(page)
        except Exception as e:
            print(f"Could not generate dashboard")
            print(f"Exception: {e}")

    def __get_substituted_template(self, template_name, variables):
        filename = f'templates/{template_name}.template'
        template = None
        try:
            with open(filename, 'r') as f:
                src = Template(f.read())
                template = src.substitute(variables)
        except Exception as e:
            print(f"Could not open file '{filename}' for substitution")
            print(f"Exception: {e}")

        return template

    def __block_template(self,
            block_number,
            block_label,
            dataset,
            filter_field,
            filter_model,
            filter_operator,
            filter_value,
            field_label,
            field_model,
            field_field,
            field_aggregation,
            field_format_type,
            field_format_pattern,
            field_format_group_separator,
            field_format_decimal_separator,
        ):
        template_name = 'vizblock.metrickpi.aml'
        variables = {
            'block_number': block_number,
            'block_label': block_label,
            'dataset': dataset,
            'filter_field': filter_field,
            'filter_model': filter_model,
            'filter_operator': filter_operator,
            'filter_value': filter_value,
            'field_label': field_label,
            'field_model': field_model,
            'field_field': field_field,
            'field_aggregation': field_aggregation,
            'field_format_type': field_format_type,
            'field_format_pattern': field_format_pattern,
            'field_format_group_separator': field_format_group_separator,
            'field_format_decimal_separator': field_format_decimal_separator,
        }
        return self.__get_substituted_template(template_name, variables)

    def __view_template(self,
            view_number,
            label,
            height,
            grid_size,
            block_title_position,
            blocks_position,
        ):
        template_name = 'view.canvaslayout.page.aml'
        variables = {
            'view_number': view_number,
            'label': label,
            'height': height,
            'grid_size': grid_size,
            'block_title_position': block_title_position,
            'blocks_position': '\n'.join(blocks_position),
        }
        return self.__get_substituted_template(template_name, variables)

    def __page_template(self,
            title,
            title_underscored,
            description,
            blocks,
            views,
        ):
        template_name = 'page.aml'

        variables = {
            'title': title,
            'title_underscored': title_underscored,
            'description': description,
            'blocks': '\n'.join(blocks),
            'views': '\n'.join(views),
        }
        return template_name, self.__get_substituted_template(template_name, variables)


def generate(file_name):
	################################
	#
	################################
    cf_sim = HolisticsKpiDashboardGenerator(file_name)
    cf_sim.generate_dashboard()
    print("Job done", file=stderr)
    return


if __name__ == "__main__":
	for arg in sys.argv[1:]:
		print(f"Processing: {arg}")
		generate(arg)
