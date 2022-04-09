"# cs5421" 
Tokenizer an input file:
python lex.py <input_filename>
Parse an input file:
python trc.py <input_filename>
Parse an input file and output the AST:
python tr_print.py <input_filename>
Generate sqls for single file:
python translation.py <input_filename>
Generate sqls for all test cases:
python translation.py
The generated sql could be tested on postgresql 14.
Use the db/*.sql to create the tables and populate the entries.
