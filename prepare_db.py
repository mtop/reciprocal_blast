#!/usr/bin/env python

table_name = 'bacteria'
blast_databases = ('Acidobacterium_capsulatum_ATCC_51196', 'Agrobacterium_tumefaciens_C58', 'Anaeromyxobacter_dehalogenans_2CP_1', 'Aquifex_aeolicus_VF5', 'Bdellovibrio_bacteriovorus_HD100', 'Bordetella_petrii_DSM_12804', 'Borrelia_garinii_PBi', 'Campylobacter_concisus_13826', 'Candidatus_Protochlamydia_amoebophila_UWE25', 'Candidatus_Solibacter_usitatus_Ellin6076', 'Chlamydia_trachomatis_434_Bu', 'Chlamydophila_abortus_S26_3', 'Chlorobium_tepidum_TLS', 'Chloroflexus_aurantiacus_J_10_fl', 'Clostridium_tetani_E88', 'Cytophaga_hutchinsonii_ATCC_33406', 'Dehalococcoides_ethenogenes_195', 'Deinococcus_radiodurans_R1', 'Delftia_acidovorans_SPH_1', 'Desulfovibrio_vulgaris_DP4', 'Ehrlichia_canis_Jake', 'Escherichia_coli_UTI89', 'Fervidobacterium_nodosum_Rt17_B1', 'Flavobacterium_johnsoniae_UW101', 'Frankia_alni_ACN14a', 'Geobacter_metallireducens_GS_15', 'Haemophilus_somnus_129PT', 'Heliobacterium_modesticaldum_Ice1', 'Herpetosiphon_aurantiacus_DSM_785', 'Legionella_pneumophila_2300_99_Alcoy', 'Leptospira_borgpetersenii_serovar_Hardjo_bovis_JB197', 'Methylibium_petroleiphilum_PM1', 'Mycobacterium_smegmatis_MC2_155', 'Mycoplasma_mobile_163K', 'Neisseria_gonorrhoeae_FA_1090', 'Nitratiruptor_SB155_2', 'Pelodictyon_phaeoclathratiforme_BU_1', 'Petrotoga_mobilis_SJ95', 'Pseudomonas_stutzeri_A1501', 'Rhodopirellula_baltica_SH_1', 'Rhodopseudomonas_palustris_CGA009', 'Rhodospirillum_rubrum_ATCC_11170', 'Roseiflexus_castenholzii_DSM_13941', 'Rubrobacter_xylanophilus_DSM_9941', 'Streptococcus_thermophilus_CNRZ1066', 'Streptomyces_avermitilis_MA_4680', 'Sulfurimonas_denitrificans_DSM_1251', 'Syntrophomonas_wolfei_Goettingen', 'Thermosipho_melanesiensis_BI429', 'Thermotoga_maritima_MSB8', 'Thermus_thermophilus_HB27', 'Treponema_denticola_ATCC_35405', 'Treponema_pallidum_DAL_1')



output_file = open('%s.sql' % table_name, 'w')

output_file.write('DROP TABLE IF EXISTS `%s`;\n' % table_name)
output_file.write('CREATE TABLE `%s` (\n' % table_name)
output_file.write('		`query_seq` varchar(12) PRIMARY KEY\n')

for name in blast_databases:
	output_file.write('		,`%s_id` varchar(100)\n' % name)
	output_file.write('		,`%s_def` varchar(500)\n' % name)
#	output_file.write('		,`%s_eval` DOUBLE(34,30) NOT NULL\n' % name)
	output_file.write('		,`%s_seq` text\n' % name)
	output_file.write('     ,`%s` varchar(5)\n' % name)

output_file.write('		);\n')
output_file.close()
