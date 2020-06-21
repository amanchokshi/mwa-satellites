"""
=========
Colormaps
=========
A set of custom colormaps used by embers.

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from scipy.interpolate import interp1d


def spectral():
    """A beautiful non-linear spectral colormap

    Spectral is not perceptually uniform and is
    only used to easily preview raw data with
    high contrast

    Returns
    -------
    :returns:
        - spectral, spectral_r - ember colormap obj:`~matplotlib.colors.Colormap`


    """

    A = np.array([219 / 256, 55 / 256, 82 / 256, 1])
    B = np.array([226 / 256, 57 / 256, 79 / 256, 1])
    C = np.array([230 / 256, 60 / 256, 76 / 256, 1])
    D = np.array([244 / 256, 109 / 256, 67 / 256, 1])
    E = np.array([253 / 256, 174 / 256, 97 / 256, 1])
    F = np.array([254 / 256, 224 / 256, 139 / 256, 1])
    G = np.array([230 / 256, 245 / 256, 152 / 256, 1])
    H = np.array([171 / 256, 221 / 256, 164 / 256, 1])
    I = np.array([102 / 256, 194 / 256, 165 / 256, 1])
    J = np.array([50 / 256, 136 / 256, 189 / 256, 1])
    K = np.array([94 / 256, 79 / 256, 162 / 256, 1])
    L = np.array([46 / 256, 67 / 256, 92 / 256, 1])
    M = np.array([38 / 256, 42 / 256, 77 / 256, 1])
    N = np.array([37 / 256, 43 / 256, 61 / 256, 1])

    ncmap = [N, M, L, K, J, I, H, G, F, E, D, C, B, A]
    c_array = []

    for i in range(len(ncmap)):
        if i != len(ncmap) - 1:
            linfit = interp1d([1, 256], np.vstack([ncmap[i], ncmap[i + 1]]), axis=0)
            for j in range(255):
                c_array.append(linfit(j + 1))

    # newcmp = ListedColormap(c_array)
    spec_cmap = ListedColormap(c_array, name="spec", N=len(c_array))
    spec_cmap_r = spec_cmap.reversed()

    return [spec_cmap, spec_cmap_r]


def jade():
    """A beautiful perceptually uniform jade colormap

    Returns
    -------
    :returns:
        - jade, jade_r - ember colormap obj:`~matplotlib.colors.Colormap`

    """

    colorlist = [
        [0.08048525330056805, 0.05201415138494773, 0.18107886855112176],
        [0.08282174108497872, 0.05548264112853812, 0.18701136971548327],
        [0.08510083379013808, 0.05893183335200911, 0.19295110050577835],
        [0.08732149679165027, 0.06236391678238993, 0.1988999668728864],
        [0.08948351372779442, 0.06578120659935585, 0.2048568371507506],
        [0.09158630556914435, 0.06918580148954842, 0.21082119130300758],
        [0.09362842795942464, 0.07257954032276293, 0.21679429113373555],
        [0.09560935498577233, 0.07596440682459804, 0.22277440676148685],
        [0.09752794289012831, 0.07934220307926157, 0.22876097274209006],
        [0.09938284674215636, 0.08271467009120442, 0.23475339391593014],
        [0.10117257181649406, 0.08608351243763912, 0.24075089154601287],
        [0.10289547247699185, 0.08945040996935877, 0.2467524877711415],
        [0.10454975102703004, 0.09281702803202968, 0.2527569887119423],
        [0.1061334566793852, 0.09618502637435938, 0.25876296625848433],
        [0.10764448481589006, 0.09955606685021534, 0.26476873860026046],
        [0.1090805767275786, 0.10293181997113154, 0.2707723495983788],
        [0.11043932005016904, 0.10631397032130063, 0.27677154714704316],
        [0.11171815013750855, 0.10970422080750591, 0.2827637607277609],
        [0.11291385345962551, 0.11310429674856487, 0.2887468683086714],
        [0.1140233083021745, 0.11651596835115913, 0.29471787846098235],
        [0.11504384858892774, 0.11994102457968481, 0.3006724844772462],
        [0.11597089088662477, 0.1233813283488848, 0.30660850772352255],
        [0.11680174115245501, 0.12683872558910916, 0.3125203302638832],
        [0.11753210249547663, 0.13031513895001925, 0.3184038841078844],
        [0.1181574480415879, 0.1338125447813214, 0.32425455000037123],
        [0.11867404554559757, 0.13733288407636784, 0.33006601551208176],
        [0.11907736155017198, 0.14087815324940609, 0.33583222502548604],
        [0.11936282780825758, 0.14445034917137684, 0.3415464303645391],
        [0.11952591076460412, 0.14805144454689917, 0.3472011730204451],
        [0.11956219574660862, 0.15168335729817528, 0.35278828230779896],
        [0.11946703477355067, 0.15534797161989095, 0.3582992390025081],
        [0.1192361182953327, 0.15904705059994143, 0.36372475837953394],
        [0.11886664197107047, 0.16278203712265407, 0.3690542044332376],
        [0.11835399462382584, 0.1665544813591542, 0.374278020169446],
        [0.11769708633606693, 0.1703652557411168, 0.3793844485150614],
        [0.11689426108150669, 0.17421509776366004, 0.3843624979497745],
        [0.11594488340102163, 0.17810436176866928, 0.38920113889145524],
        [0.11485082764232488, 0.18203274073193357, 0.39388905389112727],
        [0.11361530601755743, 0.18599943001155309, 0.39841563537326075],
        [0.11224346886066017, 0.19000302137811653, 0.40277110513165004],
        [0.11074249506992631, 0.19404149246058744, 0.4069468678334563],
        [0.10912183718013496, 0.19811218354305332, 0.4109358006442688],
        [0.10739338307745314, 0.20221180337198263, 0.414732549844077],
        [0.10557086837680585, 0.2063365897902914, 0.41833384968466514],
        [0.10366981790516067, 0.21048238687639614, 0.4217386056559858],
        [0.10170740537663389, 0.2146447428278066, 0.4249479122192987],
        [0.09970204311223499, 0.218819059805478, 0.4279649876238323],
        [0.09767282804859789, 0.22300076649675704, 0.4307949866194266],
        [0.09563957769959164, 0.22718536913793097, 0.43344476254076103],
        [0.09362188137321822, 0.23136867376098824, 0.4359225217538353],
        [0.09163911084811141, 0.23554681044865822, 0.4382374975689774],
        [0.08971021055125364, 0.2397162823192331, 0.44039963711046487],
        [0.08785341374317776, 0.24387401198668945, 0.44241929428617943],
        [0.08608604787604748, 0.24801735668271147, 0.44430696071297726],
        [0.08442437388963231, 0.2521441049770898, 0.4460730388692849],
        [0.08288345359298108, 0.25625245906452154, 0.447727660486174],
        [0.08147703924845859, 0.2603410066543993, 0.4492805492702125],
        [0.08021748052286187, 0.26440868618699465, 0.45074092430059326],
        [0.07911564571233268, 0.26845474855588225, 0.45211743879796856],
        [0.07818196546433143, 0.2724785212450291, 0.45341855485145616],
        [0.07742331496842386, 0.27647991363396385, 0.4546514629272957],
        [0.07684645341209317, 0.280458763502449, 0.4558233068453356],
        [0.07645599210316434, 0.2844151611188714, 0.45694050051595053],
        [0.07625499342910952, 0.28834931383124557, 0.4580089753858227],
        [0.07624428803082409, 0.2922616479198641, 0.4590338882994243],
        [0.0764246484998303, 0.2961524057545282, 0.46002064793302405],
        [0.07679349469917862, 0.3000222351904453, 0.4609733587165979],
        [0.07734772413661994, 0.3038716854661879, 0.46189612586822587],
        [0.078082991411866, 0.30770134701768104, 0.46279270218278606],
        [0.078993808850426, 0.3115118505312299, 0.46366648846352626],
        [0.08007372195698081, 0.3153038567985003, 0.4645205619011786],
        [0.08131549154345827, 0.31907804809298085, 0.46535770320028297],
        [0.08271127515321591, 0.3228351208997696, 0.46618042220254335],
        [0.08425280130731319, 0.3265757798371598, 0.46699098185757276],
        [0.08593153135860018, 0.3303007326185666, 0.46779142046902195],
        [0.08773880516989938, 0.334010685915416, 0.46858357220267327],
        [0.08966596826785347, 0.33770634199462096, 0.46936908588615883],
        [0.09170447943493812, 0.34138839601746424, 0.4701494421605266],
        [0.09384627191669201, 0.3450574687940023, 0.4709262383145943],
        [0.0960831566534833, 0.34871425919008814, 0.4717005822800508],
        [0.09840722058294235, 0.35235946876299223, 0.4724733819304247],
        [0.10081130535202479, 0.3559936883277908, 0.47324584798745534],
        [0.10328839922969663, 0.3596175517244634, 0.47401885251126213],
        [0.10583164048268956, 0.3632317468958568, 0.47479285720178294],
        [0.10843529606143137, 0.3668367497552385, 0.47556914313418813],
        [0.11109305466678468, 0.3704332911846674, 0.4763476646233545],
        [0.11379989493818632, 0.3740218347319917, 0.4771294894633465],
        [0.1165504277496224, 0.3776030462838571, 0.4779145781588722],
        [0.11934031236302717, 0.3811773723151275, 0.47870383244981923],
        [0.1221648808955253, 0.38474545266192633, 0.4794970619208388],
        [0.125020411942289, 0.388307718134574, 0.48029500882885473],
        [0.12790299670200686, 0.3918647459621973, 0.4810975439325174],
        [0.1308092677243089, 0.39541701876689145, 0.4819049069345677],
        [0.13373618068307982, 0.39896498572547184, 0.4827174086016704],
        [0.13668069096829463, 0.4025091728463909, 0.48353483099111366],
        [0.13964021136790725, 0.406050015101638, 0.48435734091527266],
        [0.14261235290340157, 0.4095879406664739, 0.4851850431516555],
        [0.14559477505956414, 0.41312342450853995, 0.48601767359538456],
        [0.14858543818884148, 0.416656888067347, 0.48685516603444695],
        [0.15158255724212422, 0.4201887085166255, 0.48769761426022423],
        [0.15458434439836058, 0.4237193171100199, 0.48854470146131307],
        [0.15758922166887118, 0.42724911117277475, 0.48939621005555106],
        [0.1605957694084157, 0.4307784695992068, 0.4902519372161687],
        [0.1636027244822555, 0.4343077490923155, 0.491111721839076],
        [0.16660891649172935, 0.43783730748551647, 0.491975306219297],
        [0.16961325003216388, 0.4413675088749811, 0.49284230322361616],
        [0.17261477331571376, 0.44489869096009016, 0.4937123972630855],
        [0.17561263325397278, 0.448431181362512, 0.4945852472768128],
        [0.17860606961239164, 0.4519652976547541, 0.49546048784714486],
        [0.18159442563504144, 0.4555013401990234, 0.49633777567333176],
        [0.1845771064967393, 0.4590396086408521, 0.49721668703712923],
        [0.18755358492543117, 0.4625803976464912, 0.4980967444907997],
        [0.19052342449086324, 0.4661239845401655, 0.49897749644340034],
        [0.1934862596939449, 0.46967063664691705, 0.4998584718877552],
        [0.19644179279460433, 0.4732206112796254, 0.5007391813298587],
        [0.1993897909500703, 0.47677415572168164, 0.5016191177063423],
        [0.20233008363189392, 0.48033150720616763, 0.5024977572937743],
        [0.20526256029220086, 0.4838928928924224, 0.5033745606130191],
        [0.20818716853545166, 0.48745852970998665, 0.5042489741899993],
        [0.21110391913022836, 0.49102862113430784, 0.5051204525129762],
        [0.214012859795344, 0.4946033684589058, 0.5059883847178445],
        [0.21691410080252765, 0.4981829582182889, 0.5068521777735264],
        [0.21980780356127605, 0.5017675667586048, 0.5077112273640632],
        [0.22269417927572416, 0.5053573602173034, 0.5085649188033458],
        [0.22557348769835062, 0.5089524945064459, 0.5094126279540128],
        [0.22844603596562707, 0.5125531153003807, 0.5102537221502317],
        [0.23131217750215527, 0.5161593580284437, 0.5110875611237955],
        [0.2341723109812675, 0.5197713478732411, 0.5119134979326914],
        [0.23702687933136235, 0.5233891997750044, 0.5127308798910744],
        [0.2398763687784734, 0.5270130184423942, 0.5135390494993705],
        [0.24272130791685848, 0.5306428983700274, 0.5143373453730951],
        [0.24556226680047072, 0.5342789238629028, 0.5151251031688446],
        [0.24839985604932951, 0.5379211690677673, 0.5159016565058445],
        [0.2512347259658508, 0.5415696980113599, 0.5166663378814075],
        [0.25406756565715155, 0.5452245646453509, 0.5174184795786663],
        [0.2568991009236168, 0.5488858134785958, 0.5181574105066044],
        [0.25973009315258094, 0.5525534797568642, 0.5188824561114836],
        [0.26256134496863687, 0.5562275864533538, 0.5195929608006147],
        [0.26539369184988465, 0.5599081478578057, 0.5202882642516484],
        [0.2682280037016422, 0.5635951685028145, 0.5209677102105779],
        [0.2710651839849425, 0.5672886432378643, 0.5216306473195916],
        [0.27390616884799945, 0.5709885573052456, 0.5222764299291535],
        [0.27675192626317563, 0.5746948864166812, 0.5229044188942632],
        [0.2796034551723504, 0.5784075968294059, 0.523513982355227],
        [0.28246178464433935, 0.582126645420309, 0.5241044965037023],
        [0.2853279730484085, 0.5858519797566668, 0.5246753463352459],
        [0.2882031072483145, 0.5895835381618909, 0.5252259263901075],
        [0.29108828884651083, 0.5933212565577812, 0.5257555892911342],
        [0.2939846604340613, 0.5970650547196666, 0.5262637508553819],
        [0.29689339861318054, 0.6008148391688073, 0.5267498712428699],
        [0.29981569680954845, 0.6045705119004785, 0.527213388355503],
        [0.30275277346602947, 0.6083319658590289, 0.5276537530980965],
        [0.3057058714844936, 0.6120990849338634, 0.5280704301107679],
        [0.308676257729572, 0.6158717439366385, 0.5284628985197721],
        [0.3116651844924428, 0.6196498316877389, 0.5288304574993271],
        [0.31467399818062547, 0.6234331862896855, 0.5291727658806836],
        [0.3177040383894046, 0.6272216535888611, 0.5294893603607917],
        [0.32075666502132105, 0.6310150715291278, 0.5297797826634003],
        [0.3238332465869995, 0.6348132784120495, 0.530043503342515],
        [0.32693516421157154, 0.6386161121285183, 0.5302799194545893],
        [0.33006388521640856, 0.6424233561142157, 0.530488851617822],
        [0.33322086276345425, 0.646234808783026, 0.5306699180009546],
        [0.33640753730338296, 0.6500502898970201, 0.5308224462888871],
        [0.3396254290498856, 0.6538695662347603, 0.5309461813870281],
        [0.3428760881310332, 0.6576923857459963, 0.5310409777399243],
        [0.3461610347500491, 0.6615185417790586, 0.5311061293651939],
        [0.3494818741518242, 0.6653477618992945, 0.5311414928487199],
        [0.3528402381206426, 0.6691797574550876, 0.5311470034715506],
        [0.35623773856171426, 0.6730143067272383, 0.5311217222029034],
        [0.3596761062484187, 0.676851043506187, 0.5310661929944817],
        [0.363157037432549, 0.6806897218684089, 0.5309794278887502],
        [0.36668232196586625, 0.6845299559338516, 0.5308619275145658],
        [0.3702537661054113, 0.688371459004273, 0.5307127862939564],
        [0.3738732370128696, 0.6922138036799519, 0.5305326817615184],
        [0.3775426720022207, 0.6960566802988168, 0.530320485453712],
        [0.38126403905296974, 0.6998996193218182, 0.5300769786202738],
        [0.38503939349108407, 0.7037422088073597, 0.5298018609766086],
        [0.3888708941747181, 0.7075840179095334, 0.5294946933173658],
        [0.39276071901393933, 0.7114245237641633, 0.5291560830210313],
        [0.3967111726351727, 0.7152632129656108, 0.5287860528602375],
        [0.40072468195180067, 0.7190995414849927, 0.5283845669202254],
        [0.40480381060253284, 0.7229329261285098, 0.5279515919635486],
        [0.4089511754736086, 0.7267627103199334, 0.5274877745575619],
        [0.41316958249072677, 0.7305882088422349, 0.5269934598071258],
        [0.41746199996491984, 0.7344086805786554, 0.5264691111575563],
        [0.42183157582919034, 0.7382233219015334, 0.5259153345429309],
        [0.42628165637517185, 0.7420312592199182, 0.5253329075509772],
        [0.4308159495525534, 0.7458315530961531, 0.5247222316854205],
        [0.43543825755846133, 0.7496231530434232, 0.5240846850919081],
        [0.44015264342852134, 0.7534049124762969, 0.5234219245218465],
        [0.4449637441301738, 0.7571755824501292, 0.5227350168091132],
        [0.4498764623733374, 0.7609337709003917, 0.5220258491518041],
        [0.45489611347957687, 0.76467793394586, 0.5212967794131992],
        [0.4600284135721672, 0.7684063569319022, 0.5205508850573775],
        [0.4652802364583753, 0.7721171037667829, 0.5197903041391412],
        [0.4706583986040424, 0.775808017926285, 0.5190198195405789],
        [0.47617079223836384, 0.77947665971295, 0.5182442157101737],
        [0.48182612454384705, 0.783120268274458, 0.5174694824886931],
        [0.4876345940605063, 0.7867356566770665, 0.5167020270722432],
        [0.49360651914444914, 0.7903192764479544, 0.515951933522151],
        [0.4997542969228412, 0.7938669847532194, 0.5152298780389132],
        [0.5060909937830524, 0.7973741070821171, 0.5145505062027681],
        [0.5126314280895948, 0.8008352434307523, 0.5139314572129776],
        [0.5193911391402741, 0.8042443116613637, 0.5133958296047287],
        [0.5263861804381819, 0.8075945148292144, 0.5129730996192842],
        [0.5336324426208333, 0.8108783877462027, 0.5127004910846158],
        [0.5411433393153288, 0.8140881656352382, 0.5126254166340589],
        [0.5489266893553753, 0.8172164380899232, 0.5128069977010532],
        [0.556978768743211, 0.8202575660623365, 0.5133171408735032],
        [0.5652812725304268, 0.8232088760132418, 0.5142357628132518],
        [0.5737923021481535, 0.8260734234185916, 0.5156456704889278],
        [0.5824473483043531, 0.8288610568321606, 0.5176179610409625],
        [0.5911645941995308, 0.8315883939622747, 0.5201974543340329],
        [0.599858330407827, 0.8342763530164432, 0.5233923928178723],
        [0.6084544517566809, 0.8369461925190099, 0.5271748094024599],
        [0.6168999702755021, 0.8396161731670932, 0.5314908450651845],
        [0.6251636680659655, 0.8423001907090591, 0.5362741657066403],
        [0.6332336228440085, 0.8450073628975338, 0.5414574370389853],
        [0.6411093866667529, 0.847743485848044, 0.5469782869956143],
        [0.6487998789693498, 0.8505111819429549, 0.5527833406288674],
        [0.656316890709515, 0.8533116313453962, 0.5588274350650004],
        [0.6636732101428703, 0.8561451196472208, 0.5650727734246322],
        [0.6708830645157214, 0.8590108856151255, 0.5714891332277985],
        [0.6779598489467569, 0.8619078974584948, 0.5780517482378954],
        [0.684914937069425, 0.8648353476258606, 0.5847392918208578],
        [0.6917599443374656, 0.8677919267941384, 0.5915352057061675],
        [0.6985046899134919, 0.8707765996691448, 0.5984251049468913],
        [0.705158622327226, 0.8737881445640161, 0.6053976331234809],
        [0.711729506234672, 0.8768256929917826, 0.6124424296197395],
        [0.7182246631832939, 0.8798883088960333, 0.6195510819496212],
        [0.724650949337259, 0.8829750217544431, 0.6267168107234342],
        [0.7310141145761915, 0.8860851139095216, 0.6339332654749323],
        [0.7373187760335642, 0.8892181759460619, 0.6411940604197177],
        [0.7435710067246047, 0.892373048347042, 0.6484964462881493],
        [0.749774311288356, 0.895549515072807, 0.6558350885898453],
        [0.75593256270929, 0.8987471042758479, 0.6632062461514663],
        [0.7620499697846803, 0.9019650926658775, 0.6706077607976545],
        [0.7681296325761946, 0.9052031494938839, 0.6780365298582881],
        [0.7741744830781208, 0.9084609432741264, 0.6854899069977083],
        [0.7801872926043927, 0.9117381451150655, 0.6929656429415475],
        [0.7861706795754828, 0.9150344314012067, 0.7004618329984874],
        [0.7921271175000261, 0.9183494859300595, 0.7079768706647968],
        [0.7980589429955735, 0.9216830015929358, 0.7155094066489497],
        [0.8039675555049253, 0.9250350764535149, 0.7230566721382756],
        [0.809855122400221, 0.9284053993143566, 0.7306178015167443],
        [0.8157241635130554, 0.9317934357780646, 0.7381930896022029],
        [0.8215751100440964, 0.9351996536735647, 0.7457788052451131],
        [0.8274105541549834, 0.9386234101303527, 0.7533760524581912],
        [0.8332313100794004, 0.9420649272461281, 0.7609824265673815],
        [0.839039359653216, 0.9455238038328512, 0.7685983065851764],
        [0.8448351190728174, 0.9490004259689578, 0.7762208147335705],
        [0.850620995988088, 0.9524941146669922, 0.7838517609802298],
        [0.8563970354101208, 0.9560054157499797, 0.791487766250909],
        [0.8621648437660235, 0.9595340314784105, 0.7991291785898682],
        [0.8679258122621484, 0.9630797545854436, 0.8067760394998789],
        [0.8736808458053672, 0.9666426242922864, 0.8144273857287543],
    ]

    jade_cmap = ListedColormap(colorlist, name="jade", N=len(colorlist))
    jade_cmap_r = jade_cmap.reversed()

    return [jade_cmap, jade_cmap_r]
