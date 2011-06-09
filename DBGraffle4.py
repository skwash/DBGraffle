#! /usr/bin/pythonw
#
# This file is part of DBGraffle released under the MIT license. 
# See the LICENSE for more information.
#
#	Written by Paul Davis
#	Today is August 11, 2005
#	DBGraffle for OmniGraffle 4
#	An extension of DBGraffle which is outdated
#	after a most impressive 2 day release.
#	Requires:
#
#		OmniGraffle 4
#			http://www.omnigroup.com/applications/omnigraffle/
#
#		Python
#			http://www.python.org
#
#		AppScript
#			http://freespace.virgin.net/hamish.sanderson/appscript.html
#
#		PyGreSQL
#			http://www.pygresql.org
#

import sys
import re
from appscript import *
from pg import DB

####################################################
#  Some default settings for OmniGraffle Graphics  #
####################################################

# Common to title and all types of columns.
common_props = {}
common_props[ k.shadow_vector ]			= [ 7.0, 7.0 ]
common_props[ k.shadow_fuzziness ]		= 17.45
common_props[ k.autosizing ]			= k.full
common_props[ k.text_placement ]		= k.top
common_props[ k.draws_stroke ]			= False
common_props[ k.fill ]					= k.linear_fill
common_props[ k.fill_color ]			= [ 1, 1, 1 ]
common_props[ k.gradient_center ]		= [ 0.5, 0 ]
common_props[ k.magnets ]				= [ [ 1, 0 ], [ -1, 0 ] ]
#common_props[ k.size ]					= [ 90, 14 ]

#Table Name
table_name = common_props.copy()
table_name[ k.gradient_color ]			= [ 0, 0, 1 ]

#Primary Keys
column_pkey = common_props.copy()
column_pkey[ k.gradient_color ]			= [ 1, 0, 0 ]

#Foreign Keys
column_fkey = common_props.copy()
column_fkey[ k.gradient_color ]			= [ 0, 1, 0 ]

#No Key
column_norm = common_props.copy()
column_norm[ k.gradient_color ]			= [ 1, 1, 1 ]

#Line Properties
line_props = {}
line_props[ k.line_type ]				= k.orthogonal
line_props[ k.head_type ]				= "FilledArrow"
line_props[ k.jump ]					= True

###########################################
#  The query used to gather schema data.  #
###########################################

query = """
select  c.table_name,
		c.column_name,
		c.data_type,
		c.is_nullable,
		tc.constraint_type,
		ccu.table_name as referenced_table_name,
		ccu.column_name as referenced_column_name
from	information_schema.columns as c
		left join
			information_schema.key_column_usage as kcu
			using (table_catalog, table_schema, table_name, column_name)
		left join
			information_schema.table_constraints as tc
			on (
					tc.constraint_name = kcu.constraint_name
				and tc.table_schema = kcu.table_schema
				and tc.table_name = kcu.table_name
			)
		left join
			information_schema.constraint_column_usage as ccu
			on (
					ccu.constraint_name = kcu.constraint_name
				and ccu.constraint_schema = kcu.constraint_schema
				and ccu.constraint_catalog = kcu.constraint_catalog
				and exists
				(
					select  'x'
					from	information_schema.referential_constraints as rc
					where   rc.constraint_name = kcu.constraint_name
				)
			)
where   c.table_schema = 'SCHEMA_NAME'
order   by
		c.table_name,
		c.ordinal_position
"""

#########################
#  Method definitions.  #
#########################

#Get the command line arguments
def parseArguments( argv, options ):
	"""
		I haven't taken the time to learn getopt, so I use regular expressions.
	"""
	options[ 'graffle' ] = 'OmniGraffle Professional'
	options[ 'dbhost' ] = 'localhost'
	options[ 'dbport' ] = 5432
	options[ 'dbuser' ] = ''
	options[ 'dbname' ] = ''
	options[ 'schema' ] = 'public'

	okeys = options.keys() ;
	for i in range( len( argv ) ):
		for j in range( len( okeys ) ):
			opt = re.compile( okeys[j] + '=' )
			if( opt.match( argv[i] ) ):
				options[ okeys[j] ] = opt.sub( '', argv[i] ) 

	options[ 'query' ] = re.compile( 'SCHEMA_NAME' ).sub( options[ 'schema' ], query )

#Get the information we need to draw from the database
def getSchemaInfo( options, sql_tables, sql_references ):
	"""
		Connect to the database and retrieve our schema information.
	"""
	conn = DB( options[ 'dbname' ], options[ 'dbhost' ], int( options[ 'dbport' ] ), user=options[ 'dbuser' ] ) 
	res = conn.query( options[ 'query' ] ).dictresult()

	for i in range( len( res ) ):
		ftbl		= res[i][ 'table_name' ]
		fcol		= res[i][ 'column_name' ]
		type		= res[i][ 'data_type' ] 
		nullable	= res[i][ 'is_nullable' ]
		keytype		= res[i][ 'constraint_type' ]
		ttbl		= res[i][ 'referenced_table_name' ]
		tcol		= res[i][ 'referenced_column_name' ]

		if not sql_tables.has_key( ftbl ):
			sql_tables[ ftbl ] = []

		sql_tables[ ftbl ] += [ [ fcol, type, nullable, keytype ] ] 

		if keytype == 'FOREIGN KEY' :
			sql_references += [ [ ftbl, fcol, ttbl, tcol ] ]

#Create a table in OmniGraffle from database info
def createOGTableFromSQLTable( graffle, name, sql_table, og_tables ):
	"""
		Create a table in OmniGraffle using data from the database
	"""
	shapes = []
	graphics = graffle.windows[1].document.canvases[1].graphics 

	graphics.end.make( new=k.shape, with_properties=table_name )
	shape = graphics.last.get()
	shape.text.set( name )
	shapes += [ shape ]

	use_props = None
	for i in range( len( sql_table ) ):

		if sql_table[i][3] == 'PRIMARY KEY' :
			use_props = column_pkey
		elif sql_table[i][3] == 'FOREIGN KEY' :
			use_props = column_fkey
		else :
			use_props = column_norm


		graphics.end.make( new=k.shape, with_properties=use_props )
		shape = graphics.last.get()
		shape.text.set( sql_table[i][0] ) 
		shapes += [ shape ]

	og_tables[ name ] = graffle.assemble( shapes, table_shape=[len( sql_table)+1,1] )
	og_tables[ name ].slide( by={ k.x:25,k.y:25} )

#Get the source and destination graphics for a line to be drawn
def getOGGraphicsFromReference( sql_reference, og_tables ) :
	ftbl = og_tables[ sql_reference[0] ]
	fg = None
	for col in ftbl.columns[1].graphics.get() :
		if( col.text.get() == sql_reference[1] ) :
			fg = col.get() ;
			break ;
	else:
		raise RuntimeError, "Failed to find graphic for " + sql_reference[0] + "( " + sql_reference[1] + " )"

	ttbl = og_tables[ sql_reference[2] ]
	tg = None
	for col in ttbl.columns[1].graphics.get() :
		if( col.text.get() == sql_reference[3] ) :
			tg = col.get() ;
			break ;
	else:
		raise RuntimeError, "Failed to find graphic for " + sql_reference[2] + "( " + sql_reference[3] + " )"

	return [ fg, tg ]

#Draw a line representing a reference in the database.
def createOGLineFromReference( graffle, sql_reference, og_tables ) :
	tgs = getOGGraphicsFromReference( sql_reference, og_tables )
	tgs[0].connect( to=tgs[1], with_properties=line_props )

#####################
#  Run the script.  #
#####################

options = {}

sql_tables = {}
sql_references = []

og_tables = {}

parseArguments( sys.argv, options )
graffle = app( options[ 'graffle' ] )
getSchemaInfo( options, sql_tables, sql_references )

for key in sql_tables.keys() :
	createOGTableFromSQLTable( graffle, key, sql_tables[ key ], og_tables ) 

graffle.windows[1].document.canvases[1].layout_info.properties.set( { k.random_start:False, k.animates:True, k.type:k.force_directed, k.edge_force:20.0 } )
graffle.windows[1].document.canvases[1].layout()

for i in range( len( sql_references ) ) :
	createOGLineFromReference( graffle, sql_references[ i ], og_tables )

 
