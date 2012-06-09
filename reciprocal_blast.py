#!/usr/bin/env python
# -*- coding: utf-8 -*-


###   This program uses BLAST+ (available at 
###   ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/) 
###   and the MySQL database, for a reciprocal blast analysis of 
###   multiple genome sequences. A more extensive description of 
###   the functionality of the program can be found at 
###   http://matstopel.se/notebook/Ortologous-sequences-from-NGS-data.

###   Copyright (C) 2012 Mats Töpel.
###
###   Citation: If you use this version of the program, please cite;
###   Mats Töpel (2012) Open Laboratory Notebook. www.matstopel.se
###
###   This program is free software: you can redistribute it and/or modify
###   it under the terms of the GNU General Public License as published by
###   the Free Software Foundation, either version 3 of the License, or
###   (at your option) any later version.
###   
###   This program is distributed in the hope that it will be useful,
###   but WITHOUT ANY WARRANTY; without even the implied warranty of
###   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
###   GNU General Public License for more details at
###   http://www.gnu.org/licenses/.


import ConfigParser
from optparse import OptionParser
import subprocess
import os
from Bio.Blast.Applications import NcbiblastpCommandline
from Bio.Blast import NCBIXML
from Bio import SeqIO
import MySQLdb as mdb


#####################################################
### User definded stuff (should be turned in to a ###
### commanline option or config file eventually)  ###
#####################################################


config = ConfigParser.RawConfigParser()
config.read('reciprocal_blast.cfg')


### NOT WORKING AT THE MOMENT
#host = config.get('MySQL', 'host')
#user_name = config.get('MySQL', 'user_name')
#password = config.get('MySQL', 'password')
#database_name = config.get('MySQL', 'database_name')
#db_table_name = config.get('MySQL', 'db_table_name')
#db_dir = config.get('MySQL', 'db_dir')


### Details about the MySQL databas to store the results 
### in and the genomes to use in the analysis
host = 'localhost'
user_name = 'mats'
password = 'chloroplast'
database_name = 'reciprocal_blast'
db_table_name = 'plants'
db_dir = '/home/mt258/db/Phytozome/all/'
#db_dir = '/home/mt258/db/other_plant_genomes/all/'
primary_taxon = config.get('Misc', 'primary_taxon')
secondary_taxon = config.get('Misc', 'secondary_taxon')
genomes = [primary_taxon, secondary_taxon]



##########################################

### Figure out the name(s) of the input files
def input(option, opt_str, value, parser):
	assert value is None
	value = []
	for arg in parser.rargs:
		# Stop on --foo like option
		if arg[:2] == "--" and len(arg) > 2:
			break
		# Stop on -a, but not on -3 or -3.0
		if arg[:1] == "-" and len(arg) > 1 and not floatable(arg):
			break
		value.append(arg)
	del parser.rargs[:len(value)]
	setattr(parser.values, option.dest, value)

##########################################

### Options, arguments and help
usage = "\n     %prog [-f] [input_file1 input_file2 ..]"
opts=OptionParser(usage=usage, version="%prog v.0.4")

opts.add_option("--fasta", "-f", dest="fasta_files", action="callback", 
callback=input, help="Followed by one or several input files")

#opts.add_option("--blastdbdir", "-d", dest="blast_db_dir", 
#help="Full path to the directory containing the blast databases")

options, arguments = opts.parse_args()

##########################################

### Run the actuall BLAST analyses
def blast(query_file, blast_db, out_file):
	blast_cmd = NcbiblastpCommandline(	query = query_file, 
										db = blast_db,
										out = out_file,
										task = "blastp",
										outfmt = 5,
										evalue = 1000,				# Hack. Better to check if "*.fasta" file exists.
										max_target_seqs = 1)
	# Error here = Biopython <1.55. Fix: Upgrade Biopython.
	stdout, stderr = blast_cmd()



### Run the first BLAST analyses
def prim_blast():
	print '[--] Running initial blast analyses.'
	# Take every input file ...
	for file in options.fasta_files:
		# ... and create a subdirectory with the same name 
		# if such a directory does not already exists.
		if not os.path.exists(file[:-4]):
			os.mkdir(file[:-4])
		else:
			continue
		# Blast each fasta file against each genome listed in the variable 'genomes', 
		# and create fasta files for the best BLAST matches.
		for database in genomes: 
			print '[--] Using %s to search genome %s' % (file, database)
			blast(file, '%s%s' % (db_dir, database), 
					'%s/%s.xml' % (file[:-4], database))
		os.chdir(file[:-4])
		original_result = store_result()	
		matches = 0
		for fasta_file in xml_to_fasta(file):
			blast_all_genomes(fasta_file)
			new_result = store_result()
#########################################################
#			print str(original_result)					#	Devel.
#			print str(new_result)						#
#			print len(xml_to_fasta(file))				#
#########################################################
			# Check if the new BLAST results are the same as from the original BLAST analysis
			create_entry(file[:-4])
			if original_result == new_result:
				matches += 1
				if matches == len(xml_to_fasta(file)):
					print ''
					print '###    MATCH    ###'
					print ''
					write_to_db(file[:-4], secondary_taxon, 'TRUE')
					data_from_xml(file)
					os.chdir('..')
				else:
					continue
				continue
			else:
				print ''
				print 'BREAK!'
				print ''
				write_to_db(file[:-4], secondary_taxon, 'FALSE')
				data_from_xml(file)
				matches = '0'

				os.chdir('..')
				break

### Use a fasta file as query file in BLAST 
### searches of all genomes in list "genomes".
def blast_all_genomes(file):
	for database in genomes:
		if os.stat(file)[6] == 0:     # Check if file is empty
			continue
		else:
			print '[--] Reciprocal BLAST using %s to search genome %s' % (file, database)
			blast(file, '%s%s' % (db_dir, database), '%s.xml' % database)


### Extract the sequence from a BLAST XML file
def xml_to_fasta(file):
	fasta_file_list = []
	for xml_file in list_files_and_dirs()[2]:
		if xml_file.endswith('.xml'):
			fasta_file_list.append('%s%s' % (xml_file[:-4], '.fasta'))
			run_blastdbcmd(get_hit_id(xml_file), file[:-4], xml_file)
	return fasta_file_list


### Retreive all "hit_def's" from BLAST XML files 
### and store them in the dictionary "result".
def store_result():
	result = {}
	for xml_file in list_files_and_dirs()[2]:
		if xml_file.endswith('.xml'):
			result[xml_file] = str(get_hit_def(xml_file))
	return result


### Identify files and directories in PWD
### base = PWD, 
### dirs = directories in PWD
### files = files in PWD
def list_files_and_dirs():
	base, dirs, files = iter(os.walk(os.getcwd())).next()
	return base, dirs, files


#### Find and return the "hit_id" from a Blast XML file
def get_hit_id(xml_file):
	for record in NCBIXML.parse(open(xml_file)):	# Perhaps add 'rU'
		if record.alignments:
			for align in record.alignments:
				for hsp in align.hsps:
					return align.hit_id


### Find and return the "hit_def" from a Blast XML file.
def get_hit_def(xml_file):
	for record in NCBIXML.parse(open(xml_file)):
		if record.alignments:
			for align in record.alignments:
				for hsp in align.hsps:
					return align.hit_def


### Get sequences from fasta file.
def get_sequences(file_name):
	in_file = open(file_name+'.fasta', "rU")
	for record in SeqIO.parse(in_file, "fasta"):
		return record.seq
	in_file.close()


### Run "blastdbcmd" to find the fullength sequences.
def run_blastdbcmd(entry, directory, xml_file):
	args = ["blastdbcmd", "-entry", '%s' % entry, 
			'-db', '%s/%s' % (db_dir, xml_file[:-4]), 
			"-out", '%s.fasta' % (xml_file[:-4])]
	subprocess.call(args)


### Figure out the name of the Blast db to use.
def blast_db(directory, xml_file):
	blast_db = xml_file.partition('_')[2]
	return blast_db


### Get data from xml file AND sequence from fasta file.
def data_from_xml(file):
	print '[--] Extracting data from %s.xml' % secondary_taxon.replace("'", "")
	# Write e-values, id, def and sequence to database
	write_to_db(file[:-4], '%s_id' % secondary_taxon.replace("'", ""), get_hit_id('%s.xml' % secondary_taxon.replace("'", "")))
	# Chrashes when "&apos" occures in the hit_def string. Therefore, remove ' in fasta files before running "makeblasrdb"
	write_to_db(file[:-4], '%s_def' % secondary_taxon.replace("'", ""), get_hit_def('%s.xml' % secondary_taxon.replace("'", "")))
#	write_to_db(file[:-4], '%s_eval' % secondary_taxon, get_evalue('%s.xml' % secondary_taxon))
	write_to_db(file[:-4], '%s_seq' % secondary_taxon.replace("'", ""), get_sequences(secondary_taxon.replace("'", "")))


### Create an entry defined by the query sequence file name.
def create_entry(key):
	con = mdb.connect(host, user_name, password, database_name) # Host, user name, password, database name
	with con:
		cur = con.cursor()
		cur.execute("INSERT IGNORE INTO %s(query_seq) VALUES('%s')" % (db_table_name, key))     # Remove INGNORE later

### Write the result to a MySQL database.
def write_to_db(key, column, value):
	con = mdb.connect(host, user_name, password, database_name)	# Host, user name, password, database name
	with con:
		cur = con.cursor()
		sql_string = "UPDATE %s SET %s = '%s' WHERE query_seq='%s'" % (db_table_name, column.replace("'", ""), value, key)
		cur.execute(sql_string)
		print "Number of rows updated: %d" % cur.rowcount



##########################

if __name__ == "__main__":
	prim_blast()

##########################
