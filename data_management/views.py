import json
import logging
import traceback
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Stop, Agency, Route, Shape, Calendar, CalendarDate, Trip, StopTime
import requests
import math
import io
import polyline
from typing import Optional
from queue import PriorityQueue
from datetime import datetime, date, timedelta
from django.db import transaction
import time

from dotenv import load_dotenv
import os

load_dotenv()
import copy

GRAPH_FILE = os.path.join(os.path.dirname(__file__), "graph.json")
FSTAR_FILE = os.path.join(os.path.dirname(__file__), "fstar.json")
BSTAR_FILE = os.path.join(os.path.dirname(__file__), "bstar.json")

graf = None

def save_graph_to_disk(graph):
    with open (GRAPH_FILE, "w", encoding="utf-8") as file:
        json.dump(graph, file, ensure_ascii=False)

def load_graph_from_disk():
    if not os.path.exists(GRAPH_FILE):
        return None
    with open(GRAPH_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def get_graph():
    global graf
    if graf is None:
        graf = load_graph_from_disk()
    return graf

def save_fstar_to_disk(fstar):
    with open (FSTAR_FILE, "w", encoding="utf-8") as file:
        json.dump(fstar, file, ensure_ascii=False)

def load_fstar_from_disk():
    if not os.path.exists(FSTAR_FILE):
        return None
    with open(FSTAR_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def get_fstar():
    global fstar
    fstar = load_fstar_from_disk()
    return fstar
   
def save_bstar_to_disk(bstar):
    with open (BSTAR_FILE, "w", encoding="utf-8") as file:
        json.dump(bstar, file, ensure_ascii=False)

def load_bstar_from_disk():
    if not os.path.exists(BSTAR_FILE):
        return None
    with open(BSTAR_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def get_bstar():
    global bstar
    bstar = load_bstar_from_disk()
    return bstar

@require_http_methods(["POST"])
def zisti_adresu(request):
    api_key = os.getenv('COORDS_TO_ADDRESS_API_KEY')
    data = json.loads(request.body.decode("utf-8") or "{}")
    if data == {}:
        return JsonResponse({"error": "no data provided"}, status=400)

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    latitude = data.get("lat")
    longitude = data.get("lng")
    apiUrl = 'https://geocode.maps.co/reverse?lat=' + str(latitude) + '&lon=' + str(longitude) + '&api_key=' + api_key

    try:
        call = requests.get(
            apiUrl,
            headers=headers,
            timeout=5
        )
        data = call.json()

        adresa = ''
        if 'address' in data and data['address']:
            adresa_z_dat = data.get('address')
            ulica = adresa_z_dat.get('road')
            cislo_domu = adresa_z_dat.get('house_number')
            psc = adresa_z_dat.get('postcode')
            velkomesto = adresa_z_dat.get('city')
            mesto = adresa_z_dat.get('town')
            dedina = adresa_z_dat.get('village')
            dedinka = adresa_z_dat.get('hamlet')
            stat = adresa_z_dat.get('country')

            if ulica:
                adresa += ulica + " "
                if cislo_domu:
                    adresa += cislo_domu + " "
            if velkomesto:
                adresa += velkomesto + " "
                if psc:
                    adresa += psc + " "
            elif mesto:
                adresa += mesto + " "
                if psc:
                    adresa += psc + " "
            elif dedina:
                adresa += dedina + " "
                if psc:
                    adresa += psc + " "
            elif dedinka:
                adresa += dedinka + " "
                if psc:
                    adresa += psc + " "
            if stat:
                adresa += stat
            return JsonResponse({'address': adresa})
        return JsonResponse({'error': data})

    except Exception as e:
        return JsonResponse({'error': str(e)})

logger = logging.getLogger(__name__)

def calculate_distance(location_1, location_2):
    API_KEY = os.getenv('OPEN_ROUTE_SERVICE_API_KEY')
    url = 'https://api.heigit.org/openrouteservice/v2/directions/foot-walking'

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }

    lat1 = float(location_1[0])
    lon1 = float(location_1[1])
    lat2 = float(location_2[0])
    lon2 = float(location_2[1])

    body = {
        "coordinates": [
            [lon1, lat1],
            [lon2, lat2]
        ]
    }
    
    try:   
        call = requests.post(
            url, json=body, headers=headers, timeout=10
        )
        data = call.json()

        if 'routes' in data and data['routes'] and len(data['routes']) > 0:
            var1 = data['routes'][0]['segments'][0]['distance']
            var2 = data['routes'][0]['segments'][0]['duration']
            g = list(polyline.decode(data['routes'][0]['geometry']))
            for index, _ in enumerate(g):
                g[index] = list(g[index])
                g[index][0], g[index][1] = g[index][1], g[index][0]
            return {'distance': var1, 'duration': var2, "coordinates": g}
        return {'error': data}

    except Exception as e:
        print(str(e))
        return {'error': str(e)}

def calculate_second_from_clock(time: str):
    try:
        if len(time) == 8: # HH:MM:SS
            h = int(time[:2])
            m = int(time[3:5])
            s = int(time[6:])
            return h * 3600 + m * 60 + s
        elif len(time) == 5: # HH:MM
            h = int(time[:2])
            m = int(time[3:])
            return h * 3600 + m * 60
    except:
        return 0

def calculate_duration(first: str, second: str): # time difference... hh:mm:ss - hh:mm:ss
    try:
        second = second.split(":")
        h_2 = int(second[0])
        m_2 = int(second[1])
        s_2 = int(second[2])

        first = first.split(":")
        h_1 = int(first[0])
        m_1 = int(first[1])
        s_1 = int(first[2])

        return (h_2 - h_1) * 3600 + (m_2 - m_1) * 60 + (s_2 - s_1)
    except Exception:
        return float('inf')

def update_graph(graf, fstar, bstar, radius, start, end):
    vrcholy = graf[0]
    hrany = graf[1]

    pridane_hrany = []

    radius = radius + 5 # lebo kvoli nepresnostiam v merani suradnic

    stops_v_okoli_startu = stops_in_radius(radius, start)
    if stops_v_okoli_startu is None or len(stops_v_okoli_startu) == 0:
        return "start"
    print("V okolí štartu bolo nájdených", len(stops_v_okoli_startu), "zastávok.")
    
    for s in stops_v_okoli_startu:
        coords = s["coordinates"]
        for index, _ in enumerate(coords):
            c_1 = coords[index][0]
            c_2 = coords[index][1]
            coords[index][0] = c_2
            coords[index][1] = c_1
        pridane_hrany.append(["VIRTUAL_START", s["stop_id"], s["duration_s"], 0, "walk", "walk", 1, coords])
    print("Graf bol rozšírený o", len(stops_v_okoli_startu), "peších hrán.")

    stops_v_okoli_endu = stops_in_radius(radius, end)
    if stops_v_okoli_endu is None or len(stops_v_okoli_endu) == 0:
        return "end"
    print("V okolí cieľa bolo nájdených", len(stops_v_okoli_endu), "zastávok.")

    for s in stops_v_okoli_endu:
        coords = s["coordinates"]
        for index, _ in enumerate(coords):
            c_1 = coords[index][0]
            c_2 = coords[index][1]
            coords[index][0] = c_2
            coords[index][1] = c_1
        pridane_hrany.append([s["stop_id"], "VIRTUAL_END", s["duration_s"], 0, "walk", "walk", 1, coords])
    print("Graf bol rozšírený o", len(stops_v_okoli_endu), "peších hrán.")
    updated_fstar = update_fstar(fstar, pridane_hrany)
    updated_bstar = update_bstar(bstar, pridane_hrany)
    return updated_fstar, updated_bstar

def create_graph():
    vrcholy = list(Stop.objects.all().values_list("stop_id", flat=True))
    print("V grafe sa nachádza", len(vrcholy), "vrcholov.")
    vrcholy.append("VIRTUAL_START")
    vrcholy.append("VIRTUAL_END")
    
    vsetky_spoje = (
        StopTime.objects
        .all()
        .select_related('trip', 'stop')
        .order_by('trip_id', 'stop_sequence')
        .iterator()
    )

    hrany = []

    vrchol_1: Optional[StopTime] = None
    vrchol_2: Optional[StopTime] = None

    for st in vsetky_spoje:
        if vrchol_1 is None or vrchol_1.trip_id != st.trip_id:
            vrchol_1 = st
            continue
        
        vrchol_2 = st

        at2 = vrchol_2.arrival_time
        dt1 = vrchol_1.departure_time
        cas_trasy = calculate_duration(dt1, at2)
        cas_odchodu = calculate_duration("00:00:00", dt1)

        route_id = getattr(vrchol_1.trip, "route_id", "unknown")

        hrany.append([
            vrchol_1.stop.stop_id,
            vrchol_2.stop.stop_id,
            cas_trasy,
            cas_odchodu,
            "transit",
            route_id,
            vrchol_2.trip.service_id,
            vrchol_2.trip.trip_id
        ])

        vrchol_1 = vrchol_2
    print("V grafe sa nachádza", len(hrany), "vozidlových hrán.")

    return [vrcholy, hrany]

def create_fstar():
    graph = get_graph()
    vrcholy = graph[0]
    hrany = graph[1]

    print("Začínam vytvárať množinu hrán vychádzajúcich z jednotlivých vrcholov.")
    hrany_vychadzajuce_z_vrcholov = {str(v): [] for v in vrcholy}
    for hrana in hrany:
        vstupny_vrchol = hrana[0]
        if vstupny_vrchol in hrany_vychadzajuce_z_vrcholov:
            hrany_vychadzajuce_z_vrcholov[vstupny_vrchol].append(hrana)
        else:
            hrany_vychadzajuce_z_vrcholov[str(vstupny_vrchol)] = [hrana]
    print("Množina hrán vychádzajúca z jednotlivých vrcholov bola vytvorená.")
    return hrany_vychadzajuce_z_vrcholov

def update_fstar(fstar, hrany):
    print("Pridávam hrany z VIRTUAL_STAR a z VIRTUAL_END do fstar.")
    nova_fstar = fstar.copy()
    for hrana in hrany:
        vstupny_vrchol = hrana[0]
        nova_fstar[str(vstupny_vrchol)] = nova_fstar.get(vstupny_vrchol, []) + [hrana]
    
    print("Hrany boli pridané.")
    return nova_fstar

def create_bstar():
    graph = get_graph()
    vrcholy = graph[0]
    hrany = graph[1]

    print("Začínam vytvárať množinu hrán vchádzajúcich do jednotlivých vrcholov.")
    hrany_vchadzajuce_do_vrcholov = {str(v): [] for v in vrcholy}
    for hrana in hrany:
        vystupny_vrchol = hrana[1]
        if vystupny_vrchol in hrany_vchadzajuce_do_vrcholov:
            hrany_vchadzajuce_do_vrcholov[vystupny_vrchol].append(hrana)
        else:
            hrany_vchadzajuce_do_vrcholov[str(vystupny_vrchol)] = [hrana]
    print("Množina hrán vchádzajúca do jednotlivých vrcholov bola vytvorená.")
    return hrany_vchadzajuce_do_vrcholov

def update_bstar(bstar, hrany):
    print("Pridávam hrany z VIRTUAL_STAR a z VIRTUAL_END do bstar.")
    nova_bstar = bstar.copy()
    for hrana in hrany:
        vystupny_vrchol = hrana[1]
        nova_bstar[str(vystupny_vrchol)] = nova_bstar.get(vystupny_vrchol, []) + [hrana]
    print("Hrany boli pridané.")
    return nova_bstar

def vytvor_pesie_hrany(graf):
    vrcholy = graf[0]
    hrany = graf[1]

    vsetky = Stop.objects.values('stop_id', 'stop_lat', 'stop_lon')
    limitna_vzdialenost = 200 # metrov
    print("Začínam do grafu pridávať pešie hrany...")
    celkovy_pocet = 0
    for index_1, v_1 in enumerate(vsetky):
        for index_2, v_2 in enumerate(vsetky):
            if v_1["stop_id"] == v_2["stop_id"]:
                continue

            if index_2 <= index_1:
                continue

            lat1 = v_1["stop_lat"]
            lon1 = v_1["stop_lon"]
            lat2 = v_2["stop_lat"]
            lon2 = v_2["stop_lon"]

            vzdusna_vzdialenost = calculate_air_distance([lat1, lon1], [lat2, lon2])
            if vzdusna_vzdialenost > limitna_vzdialenost * 1.1:
                continue
        
            celkovy_pocet += 1

    print('... je ' + str(celkovy_pocet) + ' zastávok, ktoré sa nachádzajú vzdušnou vzdialenosťou blízko seba.')
    print('... predpokladaný čas kontrolovania reálnej vzdialenosti zastávok: ' + str(celkovy_pocet * 2) + ' sekúnd.')

    pocet_pridanych_pesich_hran = 0
    for index_1, v_1 in enumerate(vsetky):
        for index_2, v_2 in enumerate(vsetky):
            if v_1["stop_id"] == v_2["stop_id"]:
                continue

            if index_2 <= index_1:
                continue

            API_KEY = os.getenv('OPEN_ROUTE_SERVICE_API_KEY')
            url = 'https://api.heigit.org/openrouteservice/v2/directions/foot-walking'

            headers = {
                'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                'Authorization': API_KEY,
                'Content-Type': 'application/json; charset=utf-8'
            }

            lat1 = v_1["stop_lat"]
            lon1 = v_1["stop_lon"]
            lat2 = v_2["stop_lat"]
            lon2 = v_2["stop_lon"]

            body = {
                "coordinates": [
                    [lon1, lat1],
                    [lon2, lat2]
                ]
            }
            
            vzdusna_vzdialenost = calculate_air_distance([lat1, lon1], [lat2, lon2])
            if vzdusna_vzdialenost > limitna_vzdialenost * 1.1:
                continue

            try:   
                call = requests.post(
                    url, json=body, headers=headers, timeout=10
                )
                data = call.json()

                if 'routes' in data and data['routes'] and len(data['routes']) > 0:
                    var1 = data['routes'][0]['segments'][0]['distance']
                    var2 = data['routes'][0]['segments'][0]['duration']
                    g = list(polyline.decode(data['routes'][0]['geometry']))
                    for index, _ in enumerate(g):
                        g[index] = list(g[index])
                    hrany.append([v_1["stop_id"], v_2["stop_id"], var2, 0, "walk", "walk", 1, g])
                    hrany.append([v_2["stop_id"], v_1["stop_id"], var2, 0, "walk", "walk", 1, g])
                    pocet_pridanych_pesich_hran += 1
                    if pocet_pridanych_pesich_hran % 30 == 0:
                        print("... zatiaľ bolo pridaných " + str(pocet_pridanych_pesich_hran) + " hrán ...")
                    time.sleep(2) # kedze mam limit 40 requestov za minutu (dala som zdrzanie schvalne trosku viac. preventivne)
            except Exception as e:
                print(str(e))

    print("Do grafu bolo pridaných", pocet_pridanych_pesich_hran, "peších hrán.")
    return [vrcholy, hrany]

def to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise ValueError("Unsupported date type")

# kedy je cas v sekundach
def algoritmus_na_hladanie_k_najkratsich_ciest_odchod(graf, fstar, kedy: int, den_odchodu: str, K: int, pocet_prestupovani: int):
    vrcholy = graf[0]
    hrany = graf[1]

    # v pythone, pondelok = 0, utorok = 1, ..., nedela = 6
    den_odchodu = to_date(den_odchodu)
    vcerajsok = den_odchodu - timedelta(days=1)
    den_v_tyzdni_index = den_odchodu.weekday() 
    den_v_tyzdni_string = ""
    vcerajsok_string = ""
    match den_v_tyzdni_index:
        case 0:
            den_v_tyzdni_string = 'monday'
            vcerajsok_string = 'sunday'
        case 1:
            den_v_tyzdni_string = 'tuesday'
            vcerajsok_string = 'monday'
        case 2:
            den_v_tyzdni_string = 'wednesday'
            vcerajsok_string = 'tuesday'
        case 3:
            den_v_tyzdni_string = 'thursday'
            vcerajsok_string = 'wednesday'
        case 4:
            den_v_tyzdni_string = 'friday'
            vcerajsok_string = 'thursday'
        case 5:
            den_v_tyzdni_string = 'saturday'
            vcerajsok_string = 'friday'
        case 6:
            den_v_tyzdni_string = 'sunday'
            vcerajsok_string = 'saturday'

    premavka_1_dnes = dict(CalendarDate.objects.filter(date=den_odchodu).values_list('service_id', 'exception_type'))
    premavka_1_vcera = dict(CalendarDate.objects.filter(date=vcerajsok).values_list('service_id', 'exception_type'))

    premavka_2_vsetko_dnes = Calendar.objects.values_list(
        'service_id', 
        'start_date', 
        'end_date', 
        den_v_tyzdni_string
    ).iterator()

    premavka_2_vsetko_vcerajsok = Calendar.objects.values_list(
        'service_id', 
        'start_date', 
        'end_date', 
        vcerajsok_string
    ).iterator()

    premavka_2_dnes = {}
    for i in premavka_2_vsetko_dnes:
        service_id = i[0]
        start_date = i[1]
        end_date = i[2]
        exception = i[3]

        if start_date > den_odchodu or end_date < den_odchodu:
            continue

        premavka_2_dnes[service_id] = exception

    premavka_2_vcerajsok = {}
    for i in premavka_2_vsetko_vcerajsok:
        service_id = i[0]
        start_date = i[1]
        end_date = i[2]
        exception = i[3]
        
        if start_date > vcerajsok or end_date < vcerajsok:
            continue

        premavka_2_vcerajsok[service_id] = exception

    # KROK 1
    mnozina_definitivnych_znaciek = [[] for _ in vrcholy]
    u = vrcholy.index("VIRTUAL_START")
                                           #  t   k x x_k   pocet prestupov    route_id  arrival    trip_id
    mnozina_definitivnych_znaciek[u].append([kedy,1,u,0,      0,               None,   kedy,    0,     None])
    v = vrcholy.index("VIRTUAL_END")
    prioritny_front_E = PriorityQueue()
    for h in fstar.get(str(vrcholy[u]), []):
        if vrcholy.index(h[0]) != u:
            continue
                                                                    # h[5] = route_id   departure kolko casu stravim v buse?    trip_id
        prioritny_front_E.put([h[2] + kedy, vrcholy.index(h[1]), u, 1, h[5],            kedy,     h[2],                         h[7]])
    while True:
        # KROK 2
        if prioritny_front_E.empty():
            break
        prvok_s_t_min = prioritny_front_E.get()
        
        t_min = prvok_s_t_min[0]
        w_min = prvok_s_t_min[1]
        x_min = prvok_s_t_min[2]
        w_k_min = prvok_s_t_min[3]
        route_id = prvok_s_t_min[4]
        departure_time = prvok_s_t_min[5]
        cas_v_MDH = prvok_s_t_min[6]
        trip_id = prvok_s_t_min[7]
        
        pocet_prestupov_doteraz = None
        obsahuje_dva_pesie_useky_po_sebe = False
        for i in mnozina_definitivnych_znaciek[x_min]:
            if i[1] == w_k_min:
                pocet_prestupov_doteraz = i[4]
                if trip_id != i[8] and route_id != "walk" and i[5] != "walk":
                    pocet_prestupov_doteraz += 1
                elif route_id != "walk" and i[5] == "walk" and vrcholy[i[2]] != "VIRTUAL_START":
                    pocet_prestupov_doteraz += 1
                if route_id == "walk" and i[5] == "walk":
                    obsahuje_dva_pesie_useky_po_sebe = True
                break

        if obsahuje_dva_pesie_useky_po_sebe:
            continue

        if pocet_prestupov_doteraz != None and pocet_prestupov_doteraz > pocet_prestupovani:
            continue

        if len(mnozina_definitivnych_znaciek[w_min]) < K:
            k = len(mnozina_definitivnych_znaciek[w_min]) + 1
            mnozina_definitivnych_znaciek[w_min].append([t_min, k, x_min, w_k_min, pocet_prestupov_doteraz, route_id, departure_time, cas_v_MDH, trip_id])
            
            for h in fstar.get(str(vrcholy[w_min]), []):
                if vrcholy.index(h[0]) != w_min:
                    continue

                cas_na_prestup = 0
                if h[4] == "transit" and trip_id is not None and trip_id != h[7]:
                    cas_na_prestup = 60
        
                service_id = h[6]
                
                patri_do_cesty = False
                vrchol_v = w_min
                sledovane_k = k
                while vrchol_v != u:
                    if h[1] == vrcholy[vrchol_v]:
                        patri_do_cesty = True
                        break
                    for znacka in mnozina_definitivnych_znaciek[vrchol_v]:
                        if znacka[1] == sledovane_k:
                            vrchol_v = znacka[2]
                            sledovane_k = znacka[3]
                            break
                if not patri_do_cesty:
                    if h[4] == "walk":
                        prioritny_front_E.put([t_min + h[2], vrcholy.index(h[1]), w_min, k, h[5], t_min, h[2], h[7]])

                    elif h[4] == "transit":
                        mozne_realne_casy = []
                        spoj_jazdi = False
                        # DNESNA PREMAVKA
                        if (service_id in premavka_1_dnes.keys()
                            and premavka_1_dnes[service_id] == '1') or (service_id not in premavka_1_dnes.keys()
                                                                        and service_id in premavka_2_dnes
                                                                        and premavka_2_dnes.get(service_id) == "1"):
                            spoj_jazdi = True
                            if h[3] >= t_min + cas_na_prestup:
                                mozne_realne_casy.append(h[3])
                        
                        # VCERAJSIA PREMAVKA
                        if (service_id in premavka_1_vcera.keys()
                            and premavka_1_vcera[service_id] == '1') or (service_id not in premavka_1_vcera.keys()
                                                                        and service_id in premavka_2_vcerajsok
                                                                        and premavka_2_vcerajsok.get(service_id) == "1"):
                            spoj_jazdi = True
                            r_h_3 = h[3] - 24 * 60 * 60
                            if r_h_3 >= t_min + cas_na_prestup:
                                mozne_realne_casy.append(r_h_3)
                        
                        if not spoj_jazdi or len(mozne_realne_casy) == 0:
                            continue

                        realne_h_3 = min(mozne_realne_casy)
                        prioritny_front_E.put([h[2] + realne_h_3, vrcholy.index(h[1]), w_min, k, h[5], realne_h_3, h[2], h[7]])
                            

        # KROK 3
        if prioritny_front_E.qsize() != 0 and len(mnozina_definitivnych_znaciek[v]) < K:
            pass
        else:
            break

    # rekonstrukcia najkratsich u-v ciest
    vysledne_cesty = mnozina_definitivnych_znaciek[v]
    najkratsie_cesty = []
    for k in range(len(vysledne_cesty)):
        m_k = []
        dlzka_cesty = vysledne_cesty[k][0]
        poradove_cislo_cesty = vysledne_cesty[k][1]
        predposledny_vrchol = vysledne_cesty[k][2]
        poradove_cislo_cesty_do_predposledneho_vrcholu = vysledne_cesty[k][3]
        pocet_prestupov = vysledne_cesty[k][4]
        route = vysledne_cesty[k][5]
        departure_time = vysledne_cesty[k][6]
        cas_prechod_hranou = vysledne_cesty[k][7]
        trip_id = vysledne_cesty[k][8]
        m_k.append(vrcholy[v])
        m_k.append(route)
        m_k.append(departure_time)
        m_k.append(cas_prechod_hranou)
        m_k.append(trip_id)
        while predposledny_vrchol != u:
            m_k.append(vrcholy[predposledny_vrchol])
            predchadzajuci_vrchol = mnozina_definitivnych_znaciek[predposledny_vrchol]
            for j in predchadzajuci_vrchol:
                if j[1] != poradove_cislo_cesty_do_predposledneho_vrcholu:
                    continue
                predposledny_vrchol = j[2]
                poradove_cislo_cesty_do_predposledneho_vrcholu = j[3]
                route = j[5]
                departure_time = j[6]
                cas_prechod_hranou = j[7]
                trip_id = j[8]
                m_k.append(route)
                m_k.append(departure_time)
                m_k.append(cas_prechod_hranou)
                m_k.append(trip_id)
                break
        m_k.append(vrcholy[u])
        najkratsie_cesty.append([m_k[::-1], dlzka_cesty, pocet_prestupov])
        
    return najkratsie_cesty

def algoritmus_na_hladanie_k_najkratsich_ciest_prichod(graf, bstar, kedy: int, den_odchodu: str, K: int, pocet_prestupovani: int):
    vrcholy = graf[0]
    hrany = graf[1]

    # v pythone, pondelok = 0, utorok = 1, ..., nedela = 6
    den_odchodu = to_date(den_odchodu)
    vcerajsok = den_odchodu - timedelta(days=1)
    den_v_tyzdni_index = den_odchodu.weekday() 
    den_v_tyzdni_string = ""
    vcerajsok_string = ""
    match den_v_tyzdni_index:
        case 0:
            den_v_tyzdni_string = 'monday'
            vcerajsok_string = 'sunday'
        case 1:
            den_v_tyzdni_string = 'tuesday'
            vcerajsok_string = 'monday'
        case 2:
            den_v_tyzdni_string = 'wednesday'
            vcerajsok_string = 'tuesday'
        case 3:
            den_v_tyzdni_string = 'thursday'
            vcerajsok_string = 'wednesday'
        case 4:
            den_v_tyzdni_string = 'friday'
            vcerajsok_string = 'thursday'
        case 5:
            den_v_tyzdni_string = 'saturday'
            vcerajsok_string = 'friday'
        case 6:
            den_v_tyzdni_string = 'sunday'
            vcerajsok_string = 'saturday'

    premavka_1_dnes = dict(CalendarDate.objects.filter(date=den_odchodu).values_list('service_id', 'exception_type'))
    premavka_1_vcera = dict(CalendarDate.objects.filter(date=vcerajsok).values_list('service_id', 'exception_type'))

    premavka_2_vsetko_dnes = Calendar.objects.values_list(
        'service_id', 
        'start_date', 
        'end_date', 
        den_v_tyzdni_string
    ).iterator()

    premavka_2_vsetko_vcerajsok = Calendar.objects.values_list(
        'service_id', 
        'start_date', 
        'end_date', 
        vcerajsok_string
    ).iterator()

    premavka_2_dnes = {}
    for i in premavka_2_vsetko_dnes:
        service_id = i[0]
        start_date = i[1]
        end_date = i[2]
        exception = i[3]

        if start_date > den_odchodu or end_date < den_odchodu:
            continue

        premavka_2_dnes[service_id] = exception

    premavka_2_vcerajsok = {}
    for i in premavka_2_vsetko_vcerajsok:
        service_id = i[0]
        start_date = i[1]
        end_date = i[2]
        exception = i[3]

        if start_date > vcerajsok or end_date < vcerajsok:
            continue

        premavka_2_vcerajsok[service_id] = exception

    # KROK 1
    mnozina_definitivnych_znaciek = [[] for _ in vrcholy]
    u = vrcholy.index("VIRTUAL_START")
    v = vrcholy.index("VIRTUAL_END")
                                           #  t   k x x_k   pocet prestupov    route_id  arrival    trip_id
    mnozina_definitivnych_znaciek[v].append([kedy,1,v,0,      0,               None,   kedy,  0,      None])
    prioritny_front_E = PriorityQueue()
    for h in bstar.get(str(vrcholy[v]), []):
        if vrcholy.index(h[1]) != v:
            continue
                                                                     # h[5] = route_id   departure kolko casu stravim v buse?    trip_id
        prioritny_front_E.put([0 - kedy + h[2], vrcholy.index(h[0]), v, 1, h[5],            kedy,     h[2],                         h[7]])
    while True:
        # KROK 2
        if prioritny_front_E.empty():
            break

        prvok_s_t_min = prioritny_front_E.get()
        
        t_min = prvok_s_t_min[0]
        w_min = prvok_s_t_min[1]
        x_min = prvok_s_t_min[2]
        w_k_min = prvok_s_t_min[3]
        route_id = prvok_s_t_min[4]
        departure_time = prvok_s_t_min[5]
        cas_v_MDH = prvok_s_t_min[6]
        trip_id = prvok_s_t_min[7]

        pocet_prestupov_doteraz = None
        obsahuje_dva_pesie_useky_po_sebe = False
        for i in mnozina_definitivnych_znaciek[x_min]:
            if i[1] == w_k_min:
                pocet_prestupov_doteraz = i[4]
                if trip_id != i[8] and route_id != "walk" and i[5] != "walk":
                    pocet_prestupov_doteraz += 1
                elif route_id != "walk" and i[5] == "walk" and vrcholy[i[2]] != "VIRTUAL_END":
                    pocet_prestupov_doteraz += 1
                if route_id == "walk" and i[5] == "walk":
                    obsahuje_dva_pesie_useky_po_sebe = True
                break

        if obsahuje_dva_pesie_useky_po_sebe:
            continue

        if pocet_prestupov_doteraz != None and pocet_prestupov_doteraz > pocet_prestupovani:
            continue

        if len(mnozina_definitivnych_znaciek[w_min]) < K:
            k = len(mnozina_definitivnych_znaciek[w_min]) + 1
            mnozina_definitivnych_znaciek[w_min].append([0-t_min, k, x_min, w_k_min, pocet_prestupov_doteraz, route_id, departure_time, cas_v_MDH, trip_id])
            
            for h in bstar.get(str(vrcholy[w_min]), []):
                if vrcholy.index(h[1]) != w_min:
                    continue

                cas_na_prestup = 0
                if h[4] == "transit" and trip_id is not None and trip_id != h[7]:
                    cas_na_prestup = 60

                service_id = h[6]
                
                patri_do_cesty = False
                vrchol_v = w_min
                sledovane_k = k
                while vrchol_v != v:
                    if h[0] == vrcholy[vrchol_v]:
                        patri_do_cesty = True
                        break
                    for znacka in mnozina_definitivnych_znaciek[vrchol_v]:
                        if znacka[1] == sledovane_k:
                            vrchol_v = znacka[2]
                            sledovane_k = znacka[3]
                            break
                if not patri_do_cesty:
                    if h[4] == "walk":
                        prioritny_front_E.put([t_min + h[2], vrcholy.index(h[0]), w_min, k, h[5], t_min,     h[2], h[7]])

                    elif h[4] == "transit":
                        mozne_realne_casy = []
                        spoj_jazdi = False
                        # DNESNA PREMAVKA
                        if (service_id in premavka_1_dnes.keys()
                            and premavka_1_dnes[service_id] == '1') or (service_id not in premavka_1_dnes.keys()
                                                                        and service_id in premavka_2_dnes
                                                                        and premavka_2_dnes.get(service_id) == "1"):
                            spoj_jazdi = True
                            if h[3] + h[2] <= abs(t_min) - cas_na_prestup:
                                mozne_realne_casy.append(h[3])
                        
                        # VCERAJSIA PREMAVKA
                        if (service_id in premavka_1_vcera.keys()
                            and premavka_1_vcera[service_id] == '1') or (service_id not in premavka_1_vcera.keys()
                                                                        and service_id in premavka_2_vcerajsok
                                                                        and premavka_2_vcerajsok.get(service_id) == "1"):
                            r_h_3 = h[3] - 24 * 60 * 60 + h[2]
                            if r_h_3 <= abs(t_min) - cas_na_prestup:
                                spoj_jazdi = True
                                mozne_realne_casy.append(h[3] - 24 * 60 * 60)
                        
                        if not spoj_jazdi or len(mozne_realne_casy) == 0:
                            continue

                        realne_h_3 = max(mozne_realne_casy)
                        prioritny_front_E.put([0 - realne_h_3, vrcholy.index(h[0]), w_min, k, h[5], realne_h_3,     h[2], h[7]])
                            

        # KROK 3
        if prioritny_front_E.qsize() != 0 and len(mnozina_definitivnych_znaciek[u]) < K:
            pass
        else:
            break

    # rekonstrukcia najkratsich u-v ciest
    vysledne_cesty = mnozina_definitivnych_znaciek[u]
    najkratsie_cesty = []
    for k in range(len(vysledne_cesty)):
        m_k = []
        dlzka_cesty = vysledne_cesty[k][0]
        poradove_cislo_cesty = vysledne_cesty[k][1]
        predposledny_vrchol = vysledne_cesty[k][2]
        poradove_cislo_cesty_do_predposledneho_vrcholu = vysledne_cesty[k][3]
        pocet_prestupov = vysledne_cesty[k][4]
        route = vysledne_cesty[k][5]
        departure_time = vysledne_cesty[k][6]
        cas_prechod_hranou = vysledne_cesty[k][7]
        trip_id = vysledne_cesty[k][8]
        m_k.append(vrcholy[u])
        m_k.append(route)
        m_k.append(departure_time)
        m_k.append(cas_prechod_hranou)
        m_k.append(trip_id)
        while predposledny_vrchol != v:
            m_k.append(vrcholy[predposledny_vrchol])
            predchadzajuci_vrchol = mnozina_definitivnych_znaciek[predposledny_vrchol]
            for j in predchadzajuci_vrchol:
                if j[1] != poradove_cislo_cesty_do_predposledneho_vrcholu:
                    continue
                predposledny_vrchol = j[2]
                poradove_cislo_cesty_do_predposledneho_vrcholu = j[3]
                route = j[5]
                departure_time = j[6]
                cas_prechod_hranou = j[7]
                trip_id = j[8]
                m_k.append(route)
                m_k.append(departure_time)
                m_k.append(cas_prechod_hranou)
                m_k.append(trip_id)
                break
        m_k.append(vrcholy[v])
        najkratsie_cesty.append([m_k[::-1], dlzka_cesty, pocet_prestupov])
        
    return najkratsie_cesty

def create_dict_for_route_id_to_route_name():
    vsetky_routes = Route.objects.all()
    dictionary = {}
    for route in vsetky_routes:
        dictionary[route.id] = route.route_short_name or route.route_long_name
    return dictionary

def create_dict_for_stop_id_to_stop_name():
    vsetky_stops = Stop.objects.all()
    dictionary = {}
    for stop in vsetky_stops:
        dictionary[stop.stop_id] = [stop.stop_name, stop.stop_lat, stop.stop_lon]
    return dictionary

@require_http_methods(["POST"])
def search_connections(request):
    loaded_graph = get_graph()
    if loaded_graph is None:
        return JsonResponse(
            {"error": "Graph is not created. Please, first load all the necessary files."},
            status=400)
    
    graf = loaded_graph.copy()
    loaded_fstar = get_fstar()
    loaded_bstar = get_bstar()
    if loaded_fstar is None:
        return JsonResponse(
            {"error": "fstar is not created. Please, first load all the necessary files."},
            status=400
        )
    fstar = loaded_fstar.copy()
    if loaded_bstar is None:
        return JsonResponse(
            {"error": "bstar is not created. Please, first load all the necessary files."},
            status=400
        )
    bstar = loaded_bstar.copy()
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        if data == {}:
            return JsonResponse({"error": "no data provided"}, status=400)

        start = data.get("start")
        end = data.get("end")
        
        if not start or not end:
            return JsonResponse({"error": "start/end are required"}, status=400)
        
        radius = float(data.get("radius", 500))
    
        pesi = calculate_distance(start, end)
        distance = pesi.get("distance")
        duration = pesi.get("duration")
        coords = pesi.get("coordinates")
        if isinstance(distance, (int, float)) and distance < radius and isinstance(coords, list):
            for index, _ in enumerate(coords):
                c_1 = coords[index][0]
                c_2 = coords[index][1]
                coords[index][0] = c_2
                coords[index][1] = c_1
            return JsonResponse({"direct_walk": "zvolená začiatočná a koncová poloha sú v pešej dostupnosti",
                                 "distance": distance,
                                 "duration": duration,
                                 "coords": coords
                                }, status=200)
        teraz = datetime.now()
        rok = str(teraz.year)
        mesiac = str(teraz.month)
        if len(mesiac) == 1:
            mesiac = "0" + str(mesiac)
        den = str(teraz.day)
        if len(den) == 1:
            den = "0" + str(den)
        den_odchodu = data.get("datum_cesty", str(rok) + "-" + str(mesiac) + "-" + str(den))
        cas_odchodu = calculate_second_from_clock(data.get("time", "00:00:00"))
        time_mode = data.get("time_mode", "odchod")
        pocet_prestupovani = int(data.get("pocet_prestupovani", 0))
        vysledok = update_graph(graf, fstar, bstar, radius, start, end)
        if vysledok == "start":
            return JsonResponse({"no_connection": "V blízkosti zvolenej začiatočnej polohy neboli nájdené žiadne zastávky."}, status=200)
        if vysledok == "end":
            return JsonResponse({"no_connection": "V blízkosti zvolenej koncovej polohy neboli nájdené žiadne zastávky."}, status=200)
        updated_fstar = vysledok[0].copy()
        updated_bstar = vysledok[1].copy()
        
        print("Začínam hľadať najkratšie cesty...")
        K = 30
        if time_mode == "odchod":
            vysledok = algoritmus_na_hladanie_k_najkratsich_ciest_odchod(graf, updated_fstar, cas_odchodu, den_odchodu, K, pocet_prestupovani) or []
            filtrovany_vysledok = filtruj_vysledky_odchod(vysledok)
        elif time_mode == "prichod":
            vysledok = algoritmus_na_hladanie_k_najkratsich_ciest_prichod(graf, updated_bstar, cas_odchodu, den_odchodu, K, pocet_prestupovani) or []
            filtrovany_vysledok = filtruj_vysledky_prichod(vysledok)
        else:
            vysledok = []
            filtrovany_vysledok = []
        print("Najkratšie trasy boli nájdené.")
        stop_id_to_stop_name = create_dict_for_stop_id_to_stop_name()
        route_id_to_route_name = create_dict_for_route_id_to_route_name()

        for index, i in enumerate(vysledok):
            if not i or not isinstance(i[0], list):
                continue

            k = 0
            for druhy, j in enumerate(i[0]):
                if j == "VIRTUAL_START" or j == "VIRTUAL_END":
                    continue

                if vysledok[index][0][druhy] == "walk":
                    k += 1
                    vysledok[index][0][druhy] = ["walk"]
                    continue

                

                if k % 5 == 4:
                    vysledok[index][0][druhy] = stop_id_to_stop_name.get(j, j)
                elif k % 5 == 3:
                    if isinstance(j, list):
                        print(k)
                        continue
                    vysledok[index][0][druhy] = [route_id_to_route_name.get(j, j)]
                elif k % 5 == 2:
                    vysledok[index][0][druhy] = [vysledok[index][0][druhy]]
                elif k % 5 == 1:
                    vysledok[index][0][druhy] = [vysledok[index][0][druhy]]
                elif k % 5 == 0:
                    vysledok[index][0][druhy] = [vysledok[index][0][druhy]]
                k += 1


        return JsonResponse({
            "status": "success",
            "filtrovane_cesty": filtrovany_vysledok,
        })
    except Exception as e:
        logger.exception("search_connections failed")
        return JsonResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

def filtruj_vysledky_odchod(vysledok):
    filtrovane_vysledky = []
    stvorice = [] # [prichod, odchod, celkovy_cas, pocet_prestupov]
    for v in vysledok:
        trasa = v[0]
        pocet_prestupov = v[2]
        f_vysledok = []
        f_vysledok.append(trasa)

        odchod = (trasa[8] - trasa[2]) - (trasa[8] - trasa[2]) % 60
        prichod = (trasa[-3] + trasa[-4]) - (trasa[-3] + trasa[-4]) % 60 + 60
        celkovy_cas = prichod - odchod

        stvorice.append([odchod, prichod, celkovy_cas, pocet_prestupov])

    omitted = []
    for index_1, t_1 in enumerate(stvorice):
        for index_2, t_2 in enumerate(stvorice):
            if index_1 == index_2:
                continue

            if index_2 in omitted or index_1 in omitted:
                continue

            # ak sú obidvoje rovnaké, tak zober tú, ktorá má menej prestupov
            if t_1[0] == t_2[0] and t_1[1] == t_2[1]:
                if t_1[3] == t_2[3]:
                    omitted.append(index_2)
                    continue
                elif t_1[3] < t_2[3]:
                    omitted.append(index_2)
                    continue
                if t_1[3] > t_2[3]:
                    omitted.append(index_1)
                    continue
            
            # ak je start time rovnaký, a pocet prestupov je rovnaky, zober tu s mensim end time
            if t_1[0] == t_2[0] and t_1[3] == t_2[3]:
                if t_1[1] < t_2[1]:
                    omitted.append(index_2)
                    continue
                if t_1[1] > t_2[1]:
                    omitted.append(index_1)
                    continue

            # ak je start time rovnaky, a pocet prestupov je vacsi, tak musi byt mensi end time
            if t_1[0] == t_2[0] and t_1[3] > t_2[3]:
                if t_1[1] > t_2[1]:
                    omitted.append(index_1)
                    continue
            
            # ak je start time menší, aj end time musí byť menší; ak nie je, zober tú s menším celkovým časom
            if t_1[0] < t_2[0] and t_1[1] >= t_2[1]:
                if t_1[2] < t_2[2]:
                    omitted.append(index_2)
                    continue
                if t_1[2] > t_2[2]:
                    omitted.append(index_1)
                    continue

    for index, _ in enumerate(stvorice):
        if index not in omitted:
            filtrovane_vysledky.append(vysledok[index])

    return filtrovane_vysledky

def filtruj_vysledky_prichod(vysledok):
    filtrovane_vysledky = []
    stvorice = [] # [prichod, odchod, celkovy_cas, pocet_prestupov]
    for v in vysledok:
        trasa = v[0]
        pocet_prestupov = v[2]
        f_vysledok = []
        f_vysledok.append(trasa)
        prichod = (trasa[2] + trasa[8] + trasa[7]) - (trasa[2] + trasa[8] + trasa[7]) % 60 + 60
        odchod = (trasa[-8] - trasa[-4]) - (trasa[-8] - trasa[-4]) % 60
        celkovy_cas = prichod - odchod

        stvorice.append([odchod, prichod, celkovy_cas, pocet_prestupov])
        
    omitted = []
    for index_1, t_1 in enumerate(stvorice):
        for index_2, t_2 in enumerate(stvorice):
            if index_1 == index_2:
                continue

            if index_2 in omitted or index_1 in omitted:
                continue

            # ak sú obidvoje rovnaké, tak zober tú, ktorá má menej prestupov -- ale bacha, asik mi tu niečo hapruje v tomto
            if t_1[0] == t_2[0] and t_1[1] == t_2[1]:
                if t_1[3] == t_2[3]:
                    omitted.append(index_2)
                elif t_1[3] < t_2[3]:
                    omitted.append(index_2)
                if t_1[3] > t_2[3]:
                    omitted.append(index_1)

            # ak je start time rovnaký, a pocet prestupov je rovnaky, zobr tu s mensim end time
            if t_1[0] == t_2[0] and t_1[3] == t_2[3]:
                if t_1[1] < t_2[1]:
                    omitted.append(index_2)
                    continue
                if t_1[1] > t_2[1]:
                    omitted.append(index_1)
                    continue
            
            # ak je start time rovnaký, a end time je menší, zober tú s menším end time
            if t_1[0] == t_2[0]:
                if t_1[1] < t_2[1]:
                    omitted.append(index_2)
                if t_1[1] > t_2[1]:
                    omitted.append(index_1)
            
            # ak je start time menší, aj end time musí byť menší; ak nie je, zober tú s menším celkovým časom
            if t_1[0] < t_2[0] and t_1[1] >= t_2[1]:
                if t_1[2] < t_2[2]:
                    omitted.append(index_2)
                if t_1[2] > t_2[2]:
                    omitted.append(index_1)

    for index, _ in enumerate(stvorice):
        if index not in omitted:
            filtrovane_vysledky.append(vysledok[index])

    return filtrovane_vysledky

def seconds_to_time_format(seconds):
    sekundy = round(seconds % 60)
    seconds = seconds - sekundy
    seconds = round(seconds / 60)
    minutes = round(seconds % 60)
    seconds = seconds - minutes
    seconds = round(seconds / 60)
    hours = round(seconds % 60)
    return str(hours) + ":" + str(minutes) + ":" + str(sekundy)

def calculate_air_distance(location_1, location_2):
    lat1 = float(location_1[0])
    lat2 = float(location_2[0])

    lon1 = float(location_1[1])
    lon2 = float(location_2[1])
    
    earth_radius = 6378.137

    distance_latitude = (lat2 - lat1) * math.pi / 180
    distance_longitude = (lon2 - lon1) * math.pi / 180

    a = math.pow(math.sin(distance_latitude / 2), 2) + \
        math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * \
        math.pow(math.sin(distance_longitude / 2), 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c * 1000 
    return distance

def stops_in_radius(radius, location):
    lat = float(location[0])
    lon = float(location[1])

    vsetky_zastavky = Stop.objects.all()
    kandidati = []
    vzdialenosti = {}

    for i in vsetky_zastavky:
        d = calculate_air_distance([i.stop_lat, i.stop_lon], [lat, lon])
        if d <= radius * 1.1:
            kandidati.append(i)
            vzdialenosti[i.stop_id] = d
    
    if len(kandidati) == 0:
        return None
    
    zoradeni_kandidati = sorted(kandidati, key=lambda stop: vzdialenosti[stop.stop_id])
    if len(zoradeni_kandidati) > 10:
        zoradeni_kandidati = zoradeni_kandidati[:10]
    vyhovujuce = []
    for s in zoradeni_kandidati:
        try:
            d = calculate_distance([lat, lon], [s.stop_lat, s.stop_lon])

            distance = d.get("distance") if isinstance(d, dict) else None
            duration = d.get("duration") if isinstance(d, dict) else None
            coords = d.get("coordinates") if isinstance(d, dict) else None

            if isinstance(distance, (int, float)) and distance <= radius and isinstance(coords, list):
                vyhovujuce.append({
                    "stop_id": s.stop_id,
                    "name": s.stop_name,
                    "latitude": s.stop_lat,
                    "longitude": s.stop_lon,
                    "distance_m": distance,
                    "duration_s": duration,
                    "coordinates": coords,
                })
        except Exception as ex:
            print(ex)
            continue

    vyhovujuce = sorted(vyhovujuce, key=lambda s: s["distance_m"])
    return vyhovujuce

def pomocna_funkcia(start, end, trip):
    start_sequences = list(StopTime.objects.filter(
            trip__trip_id = trip,
            stop__stop_name = start[0]
        ).order_by(
            'stop_sequence'
        ).values_list(
            'stop_sequence',
            flat=True
        ))
    count_start = len(start_sequences)
    
    end_sequences = list(StopTime.objects.filter(
            trip__trip_id = trip,
            stop__stop_name = end[0]
        ).order_by(
            'stop_sequence'
        ).values_list(
            'stop_sequence',
            flat=True
        ))
    count_end = len(end_sequences)

    mozne_dvojice = []
    for i in range(count_start):
        index_start = start_sequences[i]
        for j in range(count_end):
            index_end = end_sequences[j]
            if index_start > index_end:
                continue
            else:
                mozne_dvojice.append([index_start, index_end])

    rozdiel = []
    for index, _ in enumerate(mozne_dvojice):
        r = mozne_dvojice[index][1] - mozne_dvojice[index][0]
        rozdiel.append([index, r])
    
    index = 0
    min_value = float('inf')
    for i in rozdiel:
        if i[1] < min_value:
            min_value = i[1]
            index = i[0]
    vysledny_index_startu = mozne_dvojice[index][0]
    vysledny_index_endu = mozne_dvojice[index][1]

    s = start_sequences.index(vysledny_index_startu)
    e = end_sequences.index(vysledny_index_endu)
    return [s, e, vysledny_index_startu, vysledny_index_endu] # kazdy index znamena, ze od kolkateho vyskytu zastavky mam zacat vykreslvoat polyline

def trips_coordinates(trojice): # [start, end, trip_id]
    vsetky = []
    for index in range(len(trojice)):
        suradnice_linky = []
        vysledok = pomocna_funkcia(trojice[index][0], trojice[index][1], trojice[index][2])
        s = vysledok[0] + 1
        e = vysledok[1] + 1

        start_latitude = trojice[index][0][1]
        start_longitude = trojice[index][0][2]

        end_latitude = trojice[index][1][1]
        end_longitude = trojice[index][1][2]
    
        trip = trojice[index][2]
        color = trojice[index][3]
        suradnice_linky.append(color)
        target_shape_id = Trip.objects.filter(
            trip_id=trip
        ).values_list(
            'shape',
            flat=True
        ).first()

        if target_shape_id is None:
            suradnice = []
            suradnice.append([start_latitude, start_longitude])
            suradnice.append([end_latitude, end_longitude])
            suradnice_linky.append(suradnice)
        else:
            coords = list(Shape.objects.filter(
                shape_id=target_shape_id
            ).values(
                'shape_pt_lat',
                'shape_pt_lon'
            ).order_by('shape_pt_sequence'))

            if not coords:
                suradnice = []
                suradnice.append([start_latitude, start_longitude])
                suradnice.append([end_latitude, end_longitude])
                suradnice_linky.append(suradnice)
                vsetky.append(suradnice_linky)
                continue

            start_min = float('inf')
            start_index = 0
            ciel_min = float('inf')
            ciel_index = 0
            stop_sequences = list(
                StopTime.objects.filter(
                    trip__trip_id = trip,
                ).order_by(
                    'stop_sequence'
                ).values(
                    'stop_sequence',
                    'stop__stop_name',
                    'stop__stop_lat',
                    'stop__stop_lon'
                )
            )

            slovnik = {}
            beginning_index = 0
            for udaj in stop_sequences:
                indx = 0
                vzd = float('inf')
                sequence = udaj['stop_sequence']
                name = udaj['stop__stop_name']
                ltd = udaj['stop__stop_lat']
                lng = udaj['stop__stop_lon']

                for index in range(beginning_index, len(coords)):
                    coord = coords[index]
                    lat = coord['shape_pt_lat']
                    lon = coord['shape_pt_lon']
                    v = calculate_air_distance([lat, lon], [ltd, lng])
                    if v < vzd:
                        vzd = v
                        indx = index
                slovnik[sequence] = indx
                beginning_index = indx
            start_index = slovnik[vysledok[2]]
            ciel_index = slovnik[vysledok[3]]
            
            suradnice = []
            if start_index <= ciel_index:
                for index in range(start_index, ciel_index+1):
                    coord = coords[index]
                    lat = coord['shape_pt_lat']
                    lon = coord['shape_pt_lon']
                    suradnice.append([lat, lon])
            else:
                for index in range(ciel_index, start_index+1):
                    coord = coords[index]
                    lat = coord['shape_pt_lat']
                    lon = coord['shape_pt_lon']
                    suradnice.append([lat, lon])

            if len(suradnice) <= 1:
                suradnice = []
                suradnice.append([start_latitude, start_longitude])
                suradnice.append([end_latitude, end_longitude])
                suradnice_linky.append(suradnice)
                vsetky.append(suradnice_linky)
                
            suradnice_linky.append(suradnice)

        vsetky.append(suradnice_linky)
    return vsetky

@require_http_methods(["POST"])
def suradnice_mhd_trasy(request):
    data = json.loads(request.body.decode("utf-8") or "{}")
    if not data or data == {}:
        return JsonResponse({"error": "no data provided"}, status=400)

    segments = data.get("segments")


    precitane = []
    for segment in segments:
        start_stop = segment.get("start_stop")
        end_stop = segment.get("end_stop")
        trip = segment.get("trip")

        if not trip or trip == "walk":
            continue

        start = StopTime.objects.select_related("stop").filter(
            trip__trip_id=trip,
            stop__stop_name=start_stop
        ).first()
        end = StopTime.objects.select_related("stop").filter(
            trip__trip_id=trip,
            stop__stop_name=end_stop
        ).first()
        
        if start is None or start.stop is None:
            continue 
        if end is None or end.stop is None:
            continue 

        route_color = Trip.objects.filter(
            trip_id=trip
        ).values_list(
            'route__route_color', 
            flat=True
        ).first() or "FF0000"
        route_color = str(route_color).strip().lstrip("#")
        if len(route_color) != 6:
            route_color = "FF0000"
        precitane.append([[start.stop.stop_name, start.stop.stop_lat, start.stop.stop_lon],
                          [end.stop.stop_name, end.stop.stop_lat, end.stop.stop_lon],
                          trip, route_color])
    
    suradnice = trips_coordinates(precitane)

    return JsonResponse({
        "status": "success",
        "segments": suradnice
    }, status=200)

# funkcia sluziaca na precitanie riadku zo suboru a spravne oddelenie jednotlivych hodnot
def determine_data(line):
    riadok = []
    slovo = ""
    line = line.replace('\ufeff', '').strip()
    stred_slova = False
    for i in line:
        if not stred_slova and i == ',':
            riadok.append(slovo.replace('"', ''))
            stred_slova = False
            slovo = ""
            continue
        elif not stred_slova and i == '"':
            stred_slova = True
        elif stred_slova and i == '"':
            stred_slova = False
        slovo += i
    riadok.append(slovo.replace('"', ''))
    return riadok

# nacitavanie suborov
@require_http_methods(["POST"])
def load_files(request):
    global graf
    order = ['agency', 'stops', 'routes', 'calendar', 'calendar_dates', 'trips', 'stop_times', 'shapes']
    files = {
        'agency': request.FILES.get('agency_file'),
        'stops': request.FILES.get('stops_file'),
        'routes': request.FILES.get('routes_file'),
        'calendar': request.FILES.get('calendar_file'),
        'calendar_dates': request.FILES.get('calendar_dates_file'),
        'trips': request.FILES.get('trips_file'),
        'stop_times': request.FILES.get('stop_times_file'),
        'shapes': request.FILES.get('shapes_file'),
    }

    results = {}
    
    k = 0
    with transaction.atomic():
        while k < len(order):
            key = order[k]
            f = files[key]
            k += 1
            if f:
                stream = io.TextIOWrapper(f, encoding="utf-8")
                if key == 'agency':
                    results['agency'] = load_agency(stream)
                    print("Súbor agency_file bol načítaný.")
                elif key == 'stops':
                    results['stops'] = load_stops(stream)
                    print("Súbor stops_file bol načítaný.")
                elif key == 'routes':
                    results['routes'] = load_routes(stream)
                    print("Súbor routes_file bol načítaný.")
                elif key == 'calendar':
                    results['calendar'] = load_calendar(stream)
                    print("Súbor calendar_file bol načítaný.")
                elif key == 'calendar_dates':
                    results['calendar_dates'] = load_calendar_dates(stream)
                    print("Súbor calendar_dates_file bol načítaný.")
                elif key == 'shapes':
                    results['shapes'] = load_shapes(stream)
                    print("Súbor shapes_file bol načítaný.")
                elif key == 'trips':
                    results['trips'] = load_trips(stream)
                    print("Súbor trips_file bol načítaný.")
                elif key == 'stop_times':
                    results['stop_times'] = load_stop_times(stream)
                    print("Súbor stop_times_file bol načítaný.")

    graf = create_graph()
    graf = vytvor_pesie_hrany(graf)
    save_graph_to_disk(graf)
    fstar = create_fstar()
    save_fstar_to_disk(fstar)
    bstar = create_bstar()
    save_bstar_to_disk(bstar)
    return JsonResponse({"status": "done", "details": results})

def load_agency(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    while True:
        riadok = file.readline()
        if not riadok:
            break
        if not riadok.strip(): continue

        riadok = determine_data(riadok)

        agency_name = riadok[slovnik["agency_name"]]
        agency_timezone = riadok[slovnik["agency_timezone"]]
        
        if "agency_id" in slovnik:
            agency_id = riadok[slovnik["agency_id"]]
        else:
            from django.utils.text import slugify
            agency_id = slugify(agency_name)

        Agency.objects.get_or_create(
            agency_id=agency_id,
            defaults={
                "agency_name": agency_name,
                "agency_timezone": agency_timezone
            }
        )
        
    return "ok"

def load_routes(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}
    
    agency_dict = dict(Agency.objects.values_list('agency_id', 'id'))
    existing_routes = set(Route.objects.values_list('route_id', flat=True))
    new_routes = []

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue

        riadok = determine_data(riadok)
        
        route_id = riadok[slovnik["route_id"]]
        if not route_id in existing_routes:
            agency_id = agency_dict.get(riadok[slovnik["agency_id"]])
        
            if agency_id is None:
                riadok = file.readline()
                continue

            new_routes.append(Route(
                route_id = route_id,
                agency_id = agency_id,
                route_type = int(riadok[slovnik["route_type"]]),
                route_short_name = riadok[slovnik.get("route_short_name")] if "route_short_name" in slovnik else "",
                route_long_name = riadok[slovnik.get("route_long_name")] if "route_long_name" in slovnik else "",
                route_color = riadok[slovnik.get("route_color")] if "route_color" in slovnik else "FFFFFF"
            ))

            existing_routes.add(route_id)

        if len(new_routes) >= 1000:
            Route.objects.bulk_create(new_routes)
            new_routes = [] 

        riadok = file.readline()

    Route.objects.bulk_create(new_routes)
    return "Routes ok"

def load_stops(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    existing_stops = set(Stop.objects.values_list('stop_id', flat=True))
    new_stops = []

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue
        
        riadok = determine_data(riadok)
        stop_id = riadok[slovnik["stop_id"]]
        if stop_id not in existing_stops:
            new_stops.append(Stop(
                stop_id = stop_id,
                stop_lat = float(riadok[slovnik["stop_lat"]]),
                stop_lon = float(riadok[slovnik["stop_lon"]]),
                stop_name = riadok[slovnik["stop_name"]],
                location_type = riadok[slovnik.get("location_type")] if slovnik.get("location_type") is not None else "0"
            ))
            existing_stops.add(stop_id)

        if len(new_stops) >= 5000:
            Stop.objects.bulk_create(new_stops)
            new_stops = []

        riadok = file.readline()

    Stop.objects.bulk_create(new_stops)
    return "Stops ok"

def load_shapes(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    new_shapes = []
    unique_shape_ids = set()

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue
        riadok = determine_data(riadok)

        shape_id = riadok[slovnik["shape_id"]]
        unique_shape_ids.add(shape_id)

        raw_dist = riadok[slovnik["shape_dist_traveled"]].strip() if "shape_dist_traveled" in slovnik else ""
        
        new_shapes.append(Shape(
            shape_id = shape_id,
            shape_pt_sequence = int(riadok[slovnik["shape_pt_sequence"]]),
            shape_pt_lat = float(riadok[slovnik["shape_pt_lat"]]),
            shape_pt_lon = float(riadok[slovnik["shape_pt_lon"]]),
            shape_dist_traveled = float(raw_dist) if raw_dist else None
        ))

        riadok = file.readline()

    Shape.objects.filter(shape_id__in = unique_shape_ids).delete()

    size = 10_000
    for i in range(0, len(new_shapes), size):
        Shape.objects.bulk_create(new_shapes[i:i+size])

    return "Shapes ok"

def load_calendar(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    existing_calendar = set(Calendar.objects.values_list('service_id', flat=True))
    new_calendar = []

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue
        riadok = determine_data(riadok)

        service_id = riadok[slovnik["service_id"]]
        if service_id in existing_calendar:
            riadok = file.readline()
            continue

        sd = riadok[slovnik["start_date"]]
        ed = riadok[slovnik["end_date"]]
        
        new_calendar.append(Calendar(
            service_id = service_id,
            start_date = f"{sd[:4]}-{sd[4:6]}-{sd[6:]}",
            end_date = f"{ed[:4]}-{ed[4:6]}-{ed[6:]}",
            monday = riadok[slovnik["monday"]],
            tuesday = riadok[slovnik["tuesday"]],
            wednesday = riadok[slovnik["wednesday"]],
            thursday = riadok[slovnik["thursday"]],
            friday = riadok[slovnik["friday"]],
            saturday = riadok[slovnik["saturday"]],
            sunday = riadok[slovnik["sunday"]]
        ))

        existing_calendar.add(service_id)

        if len(new_calendar) >= 1000:
            Calendar.objects.bulk_create(new_calendar)
            new_calendar = []

        riadok = file.readline()
    
    Calendar.objects.bulk_create(new_calendar)
    return "Calendar ok"

def load_calendar_dates(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    new_dates = []
    service_ids = set()

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue
        riadok = determine_data(riadok)

        service_id = riadok[slovnik["service_id"]]
        service_ids.add(service_id)

        date = riadok[slovnik["date"]]
        new_dates.append(CalendarDate(
            service_id = service_id,
            date = f"{date[:4]}-{date[4:6]}-{date[6:]}",
            exception_type = riadok[slovnik["exception_type"]]
        ))

        riadok = file.readline()
    
    CalendarDate.objects.filter(service_id__in = service_ids).delete()
    
    size = 10_000
    for i in range(0, len(new_dates), size):
        CalendarDate.objects.bulk_create(new_dates[i:i + size])
    
    return "CalendarDates ok"

def load_trips(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    route_dict = dict(Route.objects.values_list('route_id', 'id'))
    existing_trips = set(Trip.objects.values_list('trip_id', flat=True))
    new_trips = []

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue
        riadok = determine_data(riadok)

        trip_id = riadok[slovnik["trip_id"]]

        if not trip_id in existing_trips:
            route_id = route_dict.get(riadok[slovnik["route_id"]])
            
            new_trips.append(Trip(
                trip_id = trip_id,
                route_id = route_id,
                service_id = riadok[slovnik["service_id"]],
                direction_id = riadok[slovnik.get("direction_id")] if "direction_id" in slovnik else "0",
                shape = riadok[slovnik.get("shape_id")] if "shape_id" in slovnik else None
            ))

            existing_trips.add(trip_id)

        if len(new_trips) >= 10_000:
            Trip.objects.bulk_create(new_trips)
            new_trips = []

        riadok = file.readline()

    Trip.objects.bulk_create(new_trips)
    return "Trips ok"

def load_stop_times(file):
    riadok = file.readline().strip()
    riadok = determine_data(riadok)
    slovnik = {hodnota: index for index, hodnota in enumerate(riadok)}

    stop_dict = dict(Stop.objects.values_list('stop_id', 'id'))
    trip_dict = dict(Trip.objects.values_list('trip_id', 'id'))
    new_stop_times = []
    trips_in_file = set()

    riadok = file.readline()
    while riadok != "":
        if not riadok.strip():
            riadok = file.readline()
            continue
        riadok = determine_data(riadok)

        trip_id = trip_dict.get(riadok[slovnik["trip_id"]])
        stop_id = stop_dict.get(riadok[slovnik["stop_id"]])

        if trip_id and stop_id:
            trips_in_file.add(riadok[slovnik["trip_id"]])
            new_stop_times.append(StopTime(
                trip_id = trip_id,
                stop_id = stop_id,
                stop_sequence = riadok[slovnik["stop_sequence"]],
                arrival_time = riadok[slovnik["arrival_time"]],
                departure_time = riadok[slovnik["departure_time"]]
            ))

        riadok = file.readline()

    if trips_in_file:
        StopTime.objects.filter(trip__trip_id__in = trips_in_file).delete()

    for st in range(0, len(new_stop_times), 10_000):
        StopTime.objects.bulk_create(new_stop_times[st:st+10_000])
        
    return "StopTimes ok"
