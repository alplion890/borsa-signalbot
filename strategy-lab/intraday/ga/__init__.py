"""Genetik optimizasyon — gate arkasinda.

GA tek basina tehlikelidir (overfit). Bu paket GA'yi SADECE aday-uretici olarak
kullanir; her aday mevcut purged-WF + DD-fail + 4/4-yil overfit gate'inden gecer.
Karar gate'in; GA yalniz arama yapar.

Moduller:
  ga_core           -> generic GA motoru (numpy)
  gate              -> overfit gate'i fitness + hard-filter olarak sarmalar
  optimize_gold_orb -> Gold ORB parametrelerini GA ile arar, gate'ten gecirir
"""
