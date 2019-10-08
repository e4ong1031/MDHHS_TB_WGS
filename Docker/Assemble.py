#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 16:39:36 2019

@author: edison
"""

import os
import re
import sys
import shutil
import subprocess
import argparse

SCRIPT_PATH = os.path.dirname( os.path.realpath( __file__ ) )

FASTQC_CMD = os.path.join( SCRIPT_PATH, "lib", "FastQC", "fastqc" )
MULTIQC_CMD = "multiqc"
CHECK_PHRED_CMD = os.path.join( SCRIPT_PATH, "bin", "checkPhredScoring.sh" )
TRIMMER_CMD = os.path.join( SCRIPT_PATH, "lib", "fastx_toolkit", "bin", "fastx_trimmer" )
FLASH_CMD = os.path.join( SCRIPT_PATH, "lib", "FLASH", "1.2.11", "flash" )
SPADES_CMD = os.path.join( SCRIPT_PATH, "lib", "SPAdes", "3.12.0", "bin", "spades.py" )

sys.path.append( SCRIPT_PATH )

class Assemble:
    
    def fastqc( self, inputFile, outputDir ):
        if not os.path.exists( os.path.join( outputDir, "FastQC" ) ):
            os.mkdir( os.path.join( outputDir, "FastQC" ) )
        subprocess.call( [FASTQC_CMD, '-o', os.path.join( outputDir, "FastQC" ), inputFile] )
        
    def multiqc( self, outputDir ):
        subprocess.call( [MULTIQC_CMD,os.path.join( outputDir, "FastQC" ), '-o', outputDir] )
        
    def trim( self, trimDir,forward, backward ):
        for file in os.listdir( trimDir ):
            untrimFile = os.path.join( trimDir, file )
            trimFile = os.path.join( trimDir, 'trim_' + file )
            phred = subprocess.Popen( [CHECK_PHRED_CMD, untrimFile], stdout=subprocess.PIPE )
            if phred.stdout.readline().decode().strip() == r'Phred+33':
                subprocess.call( [TRIMMER_CMD, '-f', forward, '-l', backward, '-i', untrimFile, '-o', trimFile, '-Q33'] )
            else:
                subprocess.call( [TRIMMER_CMD, '-f', forward, '-l', backward, '-i', untrimFile, '-o', trimFile] )
            subprocess.call( ['rm', untrimFile] )
        
    
    def combine( self, sample, tmpDir ):
        r1File = os.path.join( tmpDir, "{}_R1.fastq".format( sample ) )
        r2File = os.path.join( tmpDir, "{}_R2.fastq".format( sample ) )
        for file in os.listdir( tmpDir ):
            content = open( os.path.join( tmpDir, file ) ).read()
            if '_R1_' in file:
                open( r1File, 'a' ).write( content )
            if '_R2_' in file:
                open( r2File, 'a' ).write( content )
            subprocess.call( ['rm', os.path.join( tmpDir, file )] )
    
    def merge( self, sample, tmpDir ):
        r1File = os.path.join( tmpDir, "{}_R1.fastq".format( sample ) )
        r2File = os.path.join( tmpDir, "{}_R2.fastq".format( sample ) )
        subprocess.call( [FLASH_CMD, '-M', '130', '-x', '0.2', '-d', tmpDir, '-o', sample, r1File, r2File] )
        subprocess.call( ['rm', os.path.join( r1File )] )
        subprocess.call( ['rm', os.path.join( r2File )] )
    
    def assemble( self, sample, tmpDir ):
        subprocess.call( [SPADES_CMD, 
        '--merged', os.path.join( tmpDir, sample + '.extendedFrags.fastq' ), 
        '-1', os.path.join( tmpDir, sample + '.notCombined_1.fastq' ), 
        '-2', os.path.join( tmpDir, sample + '.notCombined_2.fastq' ), 
        '-o', tmpDir ] )
    
    def check_args( self, args ):
        if not os.path.exists( args.inputDir ):
            sys.stderr.write( "Input directory not found! Please check your input.\n" )
            exit(1)
        if not os.path.exists( args.outputDir ):
            os.mkdir( args.outputDir )
    
    def main( self ):
        try:
            parser = argparse.ArgumentParser( description="Create input data matrix from compute sequences' features in fasta format for Vaxign Prediction." )
            parser.add_argument( "--input", '-i', dest='inputDir', required=True )
            parser.add_argument( "--output", '-o', dest='outputDir', required=True )
            parser.add_argument( "--trim", '-t', dest="trimFlag", default=True )
            parser.add_argument( "--forward_trim", '-f', dest='forwardTrim', default='11' )
            parser.add_argument( "--backward_trim", '-b', dest='backwardTrim', default='145' )
            args = parser.parse_args()
            self.check_args( args )
            
            inputDir = args.inputDir
            outputDir = args.outputDir
            
            samples = []
            sampleFolder = {}
            sampleFiles = {}
            for folder in os.listdir( inputDir ):
                match = re.match( '^([\d]{2}RF[\d]{4}).*', folder )
                if match == None:
                    continue
                sampleAccession = match.group( 1 )
                samples.append( sampleAccession )
                sampleFolder[sampleAccession] = folder
                sampleFiles[sampleAccession] = []
                for file in os.listdir( os.path.join( inputDir, folder ) ):
                    sampleFiles[sampleAccession].append( file )
            
            for sample in samples:
                for sampleFile in sampleFiles[sample]:
                    self.fastqc( os.path.join( inputDir, sampleFolder[sample], sampleFile ), outputDir )
            
            self.multiqc( outputDir )
            
            if not os.path.exists( os.path.join( outputDir, "Assemble" ) ):
                os.mkdir( os.path.join( outputDir, "Assemble" ) )
            for sample in samples:
                if not os.path.exists( os.path.join( outputDir, "Assemble", sample ) ):
                    os.mkdir( os.path.join( outputDir, "Assemble", sample ) )
                tmpDir = os.path.join( outputDir, "Assemble", sample, "tmp" )
                if not os.path.exists( tmpDir ):
                    os.mkdir( tmpDir )
                for sampleFile in sampleFiles[sample]:
                    inputFile = os.path.join( inputDir, sampleFolder[sample], sampleFile )
                    tmpFile = os.path.join( tmpDir, sampleFile ).strip( ".gz" )
                    with open( tmpFile, 'w' ) as f:
                        subprocess.call( ['gunzip', '-c', inputFile ], stdout=f )
                    
                if args.trimFlag:
                    self.trim( tmpDir, args.forwardTrim, args.backwardTrim )
                
                self.combine( sample, tmpDir )
                
                self.merge( sample, tmpDir )
                
                self.assemble( sample, tmpDir )
                
                subprocess.call( ['cp', os.path.join( tmpDir, "scaffolds.fasta" ),
                                  os.path.join( outputDir, "Assemble", "{}.fasta".format( sample ) )] )
                
                shutil.rmtree( tmpDir )
                shutil.rmtree( os.path.join( outputDir, "Assemble", sample ) )
            
        except:
            print( sys.exc_info() )
        

if __name__ == "__main__":
    Assemble().main()
