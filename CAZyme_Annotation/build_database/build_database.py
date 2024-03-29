import re
import pandas as pd
import os
import argparse

def make_agr_parser():
    parser = argparse.ArgumentParser(description='This is the commandline interface for building Cazymes database')
    parser.add_argument('-i', '--input', help='The input dbCAN result tables and DNA sequences, they should have the same file name.', required=True)
    parser.add_argument('-o', '--output', help='The output directory of Cazyme databases', required=True,default=os.getcwd())
    parser.add_argument('-l','--level',help='The level tab file.')
    parser.add_argument('--multi',help='Whether keep multiple blast results?',default=False,const=True,nargs='?')
    return parser


def build_database(table,seq,output,level,flag):
    tab_file = pd.read_csv(table, sep='\t', header=None)
    tab_file.columns = ['Family_HMM', 'HMM_length', 'Query_ID', 'Query_length', 'E_value',
                        'HMM_start', 'HMM_end', 'Query_start', 'Query_end', 'Coverage']

    if not flag:
        tab_file = tab_file.sort_values('Coverage')
        tab_file = tab_file.drop_duplicates('Query_ID', keep='last')

    with open(seq, 'r') as f:
        dna_seq_file = f.read()

    basename = os.path.splitext(os.path.basename(seq))[0]

    output_fasta = os.path.join(output,basename)+'.fasta'
    output_txt = os.path.join(output, basename) + '.tax'

    if os.path.exists(output_fasta):
        os.remove(output_fasta)

    if os.path.exists(output_txt):
        os.remove(output_txt)

    with open(output_fasta,'w') as f:
        for i in range(0, tab_file.shape[0]):

            family = tab_file.iloc[i]['Family_HMM'].replace('.hmm', '')
            query_id = tab_file.iloc[i]['Query_ID']  # query gene name
            aa_start = tab_file.iloc[i]['Query_start']
            aa_end = tab_file.iloc[i]['Query_end']
            aa_length = tab_file.iloc[i]['Query_length']  # the length of amino acid
            # print('%d: %s'% (i+1,family))
            dna_seq_pattern = re.compile(r'>' + query_id + '\n(.*?)(>|\n$)',re.S)  # find the header and the sequence. we cannot replace . with [A-Z]
            try:
                dna_sequence = re.search(dna_seq_pattern, dna_seq_file).group(1).replace('\n','')  # \n will be counted as char.
            except:
                print('Did not find %s in sequence!' % family)
                continue

            if dna_sequence[-3:] in ['TAG', 'TAA', 'TGA']:  # if that is termination codon
                if (len(dna_sequence) - 3 != aa_length * 3):  # check the length
                    print("The length of %s did not match! Please check the input seqs!" % family)
                    print("In %s, the length of query sequence is %d but it should be %d" % (query_id, len(dna_sequence) - 3, aa_length * 3))
                    continue
            else:
                if (len(dna_sequence) != aa_length * 3):  # check the length
                    print("The length of %s did not match! Please check the input seqs!" % family)
                    print("In %s, the length of query sequence is %d but it should be %d" % (query_id, len(dna_sequence), aa_length * 3))
                    continue

            # print('Query Sequence: %s'%query_sequence)
            target_sequence = dna_sequence[(aa_start - 1) * 3:aa_end * 3] #extract the sequence
            # print('Target Seuqunce: %s\n'%target_sequence)

            f.write('>%s_cazy_%04d_%s\n%s\n' % (basename, i, query_id, target_sequence))


    with open(output_txt,'w') as f:
        for i in range(0, tab_file.shape[0]):
            name_pattern = re.compile(r'(GH|GT|CBM|PL|AA|CE)(\d+)(_\d+)?')
            query_id = tab_file.iloc[i]['Query_ID']
            family = tab_file.iloc[i]['Family_HMM'].replace('.hmm', '')
            cazy_tax = ''
            try:
                cazy_cat = re.search(name_pattern, family).group(1)
                cazy_num = re.search(name_pattern, family).group(2)
                # method 2
                cazy_tab = pd.read_csv(level, sep='\t')
                temp = cazy_tab.loc[cazy_tab.loc[:, 'L4'] == cazy_cat, :]

                for j in range(0, cazy_tab.shape[1]):
                    cazy_tax = cazy_tax + temp.columns[j] + '_' + temp.iloc[0, j] + ';'
                cazy_tax = cazy_tax.strip(';') + cazy_num
                '''if cazy_cat == 'GH' and int(cazy_num) in [5, 13, 30, 43]:
                    if re.search(name_pattern, family).group(3):
                        cazy_tax = cazy_tax + ';L5_' + family
                '''
            except:
                print('Find %s! What is that?' % family)
                #continue   #Shall we continue?
                cazy_tax = 'L1_Others;Others;Others;Others'


            #print(cazy_tax)
            #print('\n')
            f.write('%s_cazy_%04d_%s\t%s\n' % (basename, i, query_id, cazy_tax))

def main():
    parser = make_agr_parser()
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output
    level_path = args.level

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for f in os.listdir(input_path):
        #print(os.path.splitext(f))
        if os.path.splitext(f)[1]=='.tab':
            print(os.path.splitext(f)[0])
            dna_seq = os.path.join(input_path,os.path.splitext(f)[0]+'.fnn')
            dbCan_table = os.path.join(input_path,f)
            #print(dbCan_table)
            build_database(dbCan_table, dna_seq, output_path, level_path, args.multi)




if __name__ == '__main__':
    main()