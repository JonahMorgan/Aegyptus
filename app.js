// Egyptian Lemma Network Visualizer
let networks = [];
let currentNetwork = null;
let simulation = null;
let hoverTimeout = null;
let egyptianLemmas = {};
let demoticLemmas = {};
let copticLemmas = {};

// Map phonetic/transliteration codes to Gardiner codes
// Handles uniliteral, biliteral, and triliteral signs
function phoneticToGardiner(code) {
    const phoneticMap = {
        // UNILITERALS (single consonants)
        'A': 'G1',    // vulture - aleph
        'a': 'G1',
        'i': 'M17',   // reed
        'y': 'M18',   // double reed
        'ii': 'M18',
        'w': 'G43',   // quail chick
        'b': 'D58',   // foot
        'p': 'Q3',    // stool
        'f': 'I9',    // horned viper
        'm': 'G17',   // owl
        'n': 'N35',   // water
        'r': 'D21',   // mouth
        'h': 'O4',    // reed shelter
        'H': 'V28',   // wick (ḥ)
        's': 'O34',   // door bolt
        'S': 'N37',   // pool (š)
        'q': 'N29',   // hill slope (ḳ)
        'k': 'V31',   // basket
        'g': 'W11',   // jar stand
        't': 'X1',    // bread
        'T': 'V13',   // rope (ṯ)
        'd': 'D46',   // hand
        'D': 'I10',   // cobra (ḏ)
        
        // BILITERALS (common two-consonant combinations)
        'mA': 'U1',   // sickle - "true"
        'ms': 'F31',  // three fox skins
        'mr': 'U6',   // hoe
        'mn': 'Y5',   // gaming board
        'mi': 'G17',  // owl (sometimes used for mi)
        'nb': 'V30',  // basket (all, every, lord)
        'nn': 'N35',  // water (negative)
        'nw': 'W24',  // pot
        'nfr': 'F35', // heart+windpipe (beautiful, good)
        'nt': 'R4',   // standard (goddess Neith)
        'nTr': 'R8',  // god sign
        'pr': 'O1',   // house
        'pn': 'Z2',   // plural strokes
        'pt': 'N1',   // sky
        'ra': 'N5',   // sun
        'sw': 'G39',  // pintail duck
        'sn': 'Z1',   // stroke
        'xA': 'Aa1',  // placenta (thousand)
        'Xr': 'U1',   // sickle
        'tp': 'D1',   // head
        'Hr': 'D2',   // face
        'xpr': 'L1',  // scarab beetle
        'kA': 'D28',  // arms raised (ka, soul)
        'wn': 'F13',  // horns
        'wr': 'G36',  // swallow
        'bA': 'G29',  // jabiru (ba, soul)
        'in': 'M17',  // reed (by)
        'ir': 'D4',   // eye
        'aA': 'G1',   // vulture (great)
        'anx': 'S34', // ankh
        'wDA': 'S38', // was scepter
        'Dd': 'R11',  // djed pillar
        
        // TRILITERALS (common three-consonant combinations)  
        'mwt': 'G14', // vulture (mother, death)
        'nfr': 'F35', // heart+windpipe (beautiful)
        'anx': 'S34', // ankh (life)
        'ꜥnḫ': 'S34', // ankh with proper Unicode
        'wDA': 'S38', // was scepter (dominion)
        'wAs': 'S40', // was scepter variant
        'wꜣs': 'S40', // was scepter with Unicode
        'xpr': 'L1',  // scarab (become, transform)
        'ḫpr': 'L1',  // scarab with proper Unicode
        'HqA': 'S38', // crook (ruler)
        'ḥqꜣ': 'S38', // crook with Unicode
        'nTr': 'R8',  // god sign
        'nṯr': 'R8',  // god with proper Unicode
        'Htp': 'R4',  // offering table
        'ḥtp': 'R4',  // offering with proper Unicode
        'sxm': 'S42', // scepter
        'wsr': 'F12', // was scepter+r
        'xft': 'N28', // sand dune
        'siA': 'S32', // cloth
        'siꜣ': 'S32', // cloth with Unicode
        'sbA': 'N14', // star
        'sbꜣ': 'N14', // star with Unicode
        'nbw': 'S12', // gold collar
        'snD': 'G54', // fear
        'snḏ': 'G54', // fear with Unicode
        
        // SPECIAL/COMMON WORDS
        'imn': 'C12', // Amun
        'wsir': 'Q1', // Osiris (seat)
        'ist': 'Q1',  // Isis (seat)
        'sA': 'G38',  // son
        
        // VARIANTS (case-insensitive handling)
        'MA': 'U1',
        'NB': 'V30',
        'PR': 'O1',
        'RA': 'N5',
        'NFR': 'F35',
        'NTR': 'R8',
        'XPR': 'L1',
        'ANX': 'S34',
        'WDA': 'S38',
    };
    
    // Try exact match first
    if (phoneticMap[code]) {
        return phoneticMap[code];
    }
    
    // Try case-insensitive
    const upperCode = code.toUpperCase();
    if (phoneticMap[upperCode]) {
        return phoneticMap[upperCode];
    }
    
    // If it looks like a Gardiner code already (letter + number), return as-is
    if (/^[A-Z]a?a?\d+[A-Za-z]?$/i.test(code)) {
        return code;
    }
    
    return null;
}

// Render hieroglyphs using WikiHiero syntax with downloaded PNG images
// This converts Manuel de Codage to properly laid out hieroglyphic images
function renderHieroglyphs(mdcCode) {
    if (!mdcCode) return '';
    
    // Clean the MdC code - remove <hiero> tags
    const cleanCode = mdcCode.replace(/<\/?hiero>/g, '').trim();
    
    // WikiHiero syntax rules:
    // - (hyphen or space): horizontal separator (next to each other)
    // : (colon): superposition (stack vertically)
    // * (asterisk): juxtaposition (side by side within a superposed block)
    // ! (exclamation): new line
    
    // Split by line breaks first
    const lines = cleanCode.split('!');
    let html = '<div class="wikihiero-container" style="display: inline-flex; flex-direction: column; gap: 2px; align-items: flex-start;">';
    
    for (const line of lines) {
        if (!line.trim()) continue;
        html += '<div class="wikihiero-line" style="display: flex; flex-direction: row; gap: 2px; align-items: center;">';
        html += parseHieroLine(line.trim());
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// Parse a single line of WikiHiero syntax
function parseHieroLine(line) {
    // First, try to convert common phonetic sequences to Gardiner codes
    // This must happen BEFORE splitting, so multi-character codes aren't broken up
    let processedLine = line;
    
    // Sort by length (longest first) to match longer codes before shorter ones
    const phoneticCodes = [
        // TRILITERALS (longest first - from Wikipedia)
        ['aSA', 'I1'], ['ꜥšꜣ', 'I1'],
        ['wAH', 'V29'], ['wꜣḥ', 'V29'],
        ['wAs', 'S40'], ['wꜣs', 'S40'], ['wꜣb', 'S40'],
        ['wAD', 'M13'], ['wꜣḏ', 'M13'],
        ['wab', 'D60'], ['wꜥb', 'D60'],
        ['wHm', 'F25'], ['wḥm', 'F25'],
        ['wsr', 'F12'],
        ['wsx', 'S11'], ['wsḫ', 'S11'],
        ['wDa', 'Aa21'], ['wḏꜥ', 'Aa21'],
        ['wDb', 'N20'], ['wḏb', 'N20'], ['wdb', 'N20'],
        ['bAs', 'W2'], ['bꜣs', 'W2'],
        ['mAa', 'Aa11'], ['mꜣꜥ', 'Aa11'],
        ['mwt', 'G14'],
        ['nbw', 'S12'],
        ['nfr', 'F35'],
        ['nni', 'A17'],
        ['nTr', 'R8'], ['nṯr', 'R8'],
        ['rwD', 'T12'], ['rwḏ', 'T12'], ['rwd', 'T12'],
        ['HqA', 'S38'], ['ḥqꜣ', 'S38'],
        ['Htp', 'R4'], ['ḥtp', 'R4'],
        ['xpr', 'L1'], ['ḫpr', 'L1'],
        ['xnt', 'W17'], ['ḫnt', 'W17'],
        ['xrp', 'S42'], ['ḫrp', 'S42'],
        ['xrw', 'P8'], ['ḫrw', 'P8'],
        ['xsf', 'U34'], ['ḫsf', 'U34'],
        ['Xnm', 'W9'], ['ẖnm', 'W9'],
        ['siA', 'S32'], ['siꜣ', 'S32'],
        ['sbA', 'N14'], ['sbꜣ', 'N14'], ['dwꜣ', 'N14'],
        ['spr', 'F42'],
        ['snb', 'S29'],
        ['snD', 'G54'], ['snḏ', 'G54'], ['snd', 'G54'],
        ['sSm', 'T31'], ['sšm', 'T31'],
        ['stp', 'U21'],
        ['Sps', 'A50'], ['šps', 'A50'],
        ['Sma', 'M26'], ['šmꜥ', 'M26'],
        ['Sms', 'T18'], ['šms', 'T18'],
        ['Sna', 'U13'], ['šnꜥ', 'U13'],
        ['Szp', 'O42'], ['šzp', 'O42'],
        ['grg', 'U17'],
        ['tiw', 'G4'],
        ['dmd', 'S23'], ['dmḏ', 'S23'],
        ['dSr', 'G27'], ['dšr', 'G27'],
        ['DbA', 'T25'], ['ḏbꜣ', 'T25'], ['dbꜣ', 'T25'],
        ['anx', 'S34'], ['ꜥnḫ', 'S34'],
        ['wDA', 'S38'],
        ['NFR', 'F35'], ['ANX', 'S34'], ['WDA', 'S38'], ['XPR', 'L1'], ['NTR', 'R8'],
        
        // BILITERALS (from Wikipedia)
        ['Aw', 'F40'], ['ꜣw', 'F40'],
        ['Ab', 'U23'], ['ꜣb', 'U23'],
        ['Ax', 'G25'], ['ꜣḫ', 'G25'],
        ['iw', 'D54'],
        ['ib', 'E8'],
        ['im', 'Aa13'],
        ['in', 'A27'],
        ['ir', 'A48'],
        ['iH', 'T24'], ['iḥ', 'T24'],
        ['iz', 'M40'],
        ['As', 'Q1'],
        ['ik', 'A19'],
        ['it', 'I3'],
        ['iT', 'V15'], ['iṯ', 'V15'],
        ['aA', 'O29'], ['ꜥꜣ', 'O29'],
        ['ab', 'F16'], ['ꜥb', 'F16'],
        ['aH', 'T24'], ['ꜥḥ', 'T24'],
        ['aq', 'G35'], ['ꜥq', 'G35'],
        ['aD', 'K3'], ['ꜥḏ', 'K3'],
        ['wA', 'V4'], ['wꜣ', 'V4'],
        ['wa', 'T21'], ['wꜥ', 'T21'],
        ['wp', 'F13'],
        ['wn', 'E34'],
        ['wr', 'G36'],
        ['ws', 'F51c'],
        ['wD', 'M13'], ['wḏ', 'M13'],
        ['bA', 'G29'], ['bꜣ', 'G29'],
        ['bH', 'F18'], ['bḥ', 'F18'],
        ['pA', 'G40'], ['pꜣ', 'G40'],
        ['pr', 'O1'],
        ['pH', 'F22'], ['pḥ', 'F22'],
        ['pd', 'D56'],
        ['pD', 'T9'], ['pḏ', 'T9'],
        ['mA', 'U1'], ['mꜣ', 'U1'],
        ['mi', 'D36'],
        ['mw', 'N35a'],
        ['mm', 'G18'],
        ['mn', 'T1'],
        ['mr', 'N36'],
        ['mH', 'V22'], ['mḥ', 'V22'],
        ['ms', 'F31'],
        ['mt', 'D52'],
        ['md', 'S43'],
        ['ni', 'D35'], ['nj', 'D35'],
        ['nw', 'U19'],
        ['nb', 'V30'],
        ['nm', 'O5'],
        ['nn', 'M22a'],
        ['nr', 'H4'],
        ['nH', 'G21'], ['nḥ', 'G21'],
        ['ns', 'F20'],
        ['nD', 'Aa27'], ['nḏ', 'Aa27'],
        ['rw', 'E23'],
        ['rs', 'T13'],
        ['hb', 'U13'],
        ['HA', 'M16'], ['ḥꜣ', 'M16'],
        ['Hw', 'F18'], ['ḥw', 'F18'],
        ['Hp', 'Aa5'], ['ḥp', 'Aa5'],
        ['Hm', 'N42'], ['ḥm', 'N42'],
        ['Hn', 'M2'], ['ḥn', 'M2'],
        ['Hr', 'D2'], ['ḥr', 'D2'],
        ['Hz', 'W14'], ['ḥz', 'W14'],
        ['HD', 'T3'], ['ḥḏ', 'T3'],
        ['xA', 'L6'], ['ḫꜣ', 'L6'],
        ['xa', 'N28'], ['ḫꜥ', 'N28'],
        ['xw', 'D43'], ['ḫw', 'D43'],
        ['xm', 'R22'], ['ḫm', 'R22'],
        ['xt', 'M3'], ['ḫt', 'M3'],
        ['XA', 'K4'], ['ẖꜣ', 'K4'],
        ['Xn', 'D33'], ['ẖn', 'D33'],
        ['Xr', 'T28'], ['ẖr', 'T28'],
        ['zA', 'G39'], ['zꜣ', 'G39'],
        ['zp', 'O50'],
        ['sA', 'Aa17'], ['sꜣ', 'Aa17'],
        ['sw', 'M23'],
        ['sn', 'T22'],
        ['sk', 'V29'],
        ['st', 'F29'],
        ['sT', 'S22'], ['sṯ', 'S22'],
        ['sD', 'Z9'], ['sḏ', 'Z9'],
        ['SA', 'H7'], ['šꜣ', 'H7'],
        ['Sw', 'H6'], ['šw', 'H6'],
        ['Sm', 'N40'], ['šm', 'N40'],
        ['Sn', 'V1'], ['šn', 'V1'],
        ['Ss', 'V6'], ['šs', 'V6'],
        ['Sd', 'F30'], ['šd', 'F30'],
        ['qn', 'Aa8'],
        ['qs', 'T19'],
        ['qd', 'Aa28'],
        ['kA', 'D28'], ['kꜣ', 'D28'],
        ['kp', 'R5'],
        ['km', 'I6'],
        ['gb', 'G38'],
        ['gm', 'G28'],
        ['gs', 'Aa13'],
        ['tA', 'N16'], ['tꜣ', 'N16'],
        ['ti', 'U33'], ['tj', 'U33'],
        ['tp', 'D1'],
        ['tm', 'U15'],
        ['tr', 'M6'],
        ['TA', 'G47'], ['ṯꜣ', 'G47'],
        ['Tz', 'S24'], ['ṯz', 'S24'],
        ['di', 'D37'], ['dj', 'D37'],
        ['DA', 'U28'], ['ḏꜣ', 'U28'],
        ['Di', 'X8'], ['ḏj', 'X8'],
        ['Dw', 'N26'], ['ḏw', 'N26'],
        ['Db', 'G22'], ['ḏb', 'G22'],
        ['Dr', 'M36'], ['ḏr', 'M36'],
        ['Dd', 'R11'], ['ḏd', 'R11'],
        ['DD', 'I11'], ['ḏḏ', 'I11'],
    ];
    
    // Replace phonetic codes with Gardiner codes, but only when they're standalone
    // (not part of a larger Gardiner code like "A1")
    for (const [phonetic, gardiner] of phoneticCodes) {
        if (!phonetic || !gardiner) continue; // Skip malformed entries
        // Use word boundaries to avoid replacing parts of Gardiner codes
        // Match the code when it's between separators or at boundaries
        const regex = new RegExp(`(^|[\\s\\-:*])${phonetic}(?=[\\s\\-:*]|$)`, 'gi');
        processedLine = processedLine.replace(regex, `$1${gardiner}`);
    }
    
    // Split by horizontal separators (- or space)
    const blocks = processedLine.split(/[\s\-]+/).filter(b => b.trim());
    let html = '';
    
    for (const block of blocks) {
        if (!block) continue;
        
        // Check if this block has superposition (:) or juxtaposition (*)
        if (block.includes(':') || block.includes('*')) {
            html += parseHieroBlock(block);
        } else {
            // Single glyph
            html += renderGlyph(block);
        }
    }
    
    return html;
}

// Parse a block with superposition (:) and juxtaposition (*)
function parseHieroBlock(block) {
    // Split by colon for vertical stacking
    const verticalParts = block.split(':');
    
    let html = '<div class="wikihiero-block" style="display: flex; flex-direction: column; align-items: center;">';
    
    for (const part of verticalParts) {
        if (!part) continue;
        
        // Check if this part has juxtaposition (*)
        if (part.includes('*')) {
            const horizontalParts = part.split('*').filter(p => p.trim());
            html += '<div class="wikihiero-juxtaposed" style="display: flex; flex-direction: row; align-items: center;">';
            for (const glyph of horizontalParts) {
                html += renderGlyph(glyph);
            }
            html += '</div>';
        } else {
            html += renderGlyph(part);
        }
    }
    
    html += '</div>';
    return html;
}

// Render a single glyph as an image
function renderGlyph(code) {
    if (!code || code.trim() === '') return '';
    
    let cleanCode = code.trim();
    
    // Debug logging
    console.log('renderGlyph called with:', code);
    
    // Try to convert phonetic/transliteration codes to Gardiner codes
    const gardinerCode = phoneticToGardiner(cleanCode);
    console.log('phoneticToGardiner returned:', gardinerCode, 'for input:', cleanCode);
    
    if (gardinerCode) {
        cleanCode = gardinerCode;
    }
    
    const imagePath = `hiero_images/hiero_${cleanCode}.png`;
    console.log('Image path:', imagePath);
    
    // Return an img tag with the hieroglyph at natural resolution
    // If image fails to load, show the code in brackets
    return `<img src="${imagePath}" alt="${code.trim()}" title="${code.trim()}" class="hieroglyph-img" style="display: inline-block; vertical-align: middle;" onerror="this.style.display='none'; this.insertAdjacentHTML('afterend', '<span style=\\'font-size: 10px; color: #999; font-family: monospace;\\'>[${code.trim()}]</span>');">`;
}

// Alternative: Use Google's Noto Sans Egyptian Hieroglyphs font with proper rendering
// This requires mapping MdC codes to Unicode, which we'll do more carefully
function mdcToUnicode(mdcCode) {
    if (!mdcCode) return '';
    
    const cleanCode = mdcCode.replace(/<\/?hiero>/g, '').trim();
    
    // Simple mapping for common codes
    // We'll use a subset that we know works
    const gardinerCodepoints = {
        // Most reliable mappings
        'A1': '𓀀', 'A2': '𓀁', 'A40': '𓀪',
        'D1': '𓁶', 'D2': '𓁷', 'D4': '𓁹', 'D21': '𓂋', 'D36': '𓂝', 'D46': '𓂧', 'D54': '𓂻', 'D58': '𓂿',
        'E1': '𓃀', 'E23': '𓃭', 'E22': '𓃬',
        'F1': '𓃰', 'F4': '𓃳', 'F12': '𓃻', 'F13': '𓃽', 'F18': '𓄂', 'F20': '𓄤', 'F21': '𓄅', 'F22': '𓄆', 'F23': '𓄇', 'F27': '�', 'F31': '𓄓', 'F32': '𓄔', 'F34': '𓄖', 'F35': '𓄗', 'F40': '𓄜',
        'G1': '𓄿', 'G4': '𓅂', 'G5': '𓅃', 'G7': '𓅆', 'G14': '𓅌', 'G17': '𓅓', 'G21': '𓅜', 'G26': '𓅣', 'G27': '𓅤', 'G28': '𓅥', 'G29': '𓅦', 'G35': '𓅬', 'G36': '𓅭', 'G37': '𓅮', 'G38': '𓅯', 'G39': '𓅰', 'G40': '𓅱', 'G41': '𓅲', 'G43': '𓅴', 'G44': '𓅵',
        'I9': '𓆑', 'I10': '𓆓',
        'M1': '𓆱', 'M2': '𓆲', 'M3': '𓆳', 'M4': '𓆴', 'M8': '𓆸', 'M12': '𓆼', 'M13': '𓆽', 'M16': '𓇀', 'M17': '𓇋', 'M18': '𓇌', 'M20': '𓇎', 'M22': '𓇐', 'M23': '𓇑', 'M26': '𓇔', 'M29': '𓇗', 'M36': '𓇞', 'M40': '𓇢', 'M41': '𓇣', 'M42': '𓇤', 'M44': '𓇦',
        'N1': '𓇯', 'N5': '𓇳', 'N14': '𓇼', 'N16': '𓇾', 'N17': '𓇿', 'N18': '𓈀', 'N25': '𓈈', 'N26': '𓈉', 'N29': '𓈎', 'N31': '𓈐', 'N35': '𓈖', 'N37': '𓈘', 'N41': '𓈜',
        'O1': '𓉐', 'O4': '𓉔', 'O29': '𓊖', 'O34': '𓊨', 'O49': '𓊹',
        'P1': '𓊪', 'P8': '𓊽',
        'Q1': '𓊨', 'Q3': '𓋁',
        'R4': '𓋔', 'R7': '𓋗', 'R8': '𓋘', 'R11': '𓋜', 'R14': '𓋞',
        'S3': '𓋴', 'S12': '𓋹', 'S29': '𓌅', 'S34': '𓌓', 'S38': '𓌙', 'S39': '𓌚', 'S42': '𓌝', 'S43': '𓌞',
        'T3': '𓌙', 'T7': '𓌝', 'T8': '𓌞', 'T14': '𓌤', 'T21': '𓌳', 'T22': '𓌴', 'T28': '𓌻', 'T30': '𓌽', 'T34': '𓍁',
        'U1': '𓍁', 'U6': '𓍆', 'U7': '𓍇', 'U15': '𓍏', 'U19': '𓍓', 'U23': '𓍘', 'U28': '𓍝', 'U32': '𓍢', 'U33': '𓍣', 'U36': '𓍦',
        'V1': '𓍢', 'V2': '𓍣', 'V4': '𓍥', 'V6': '𓍧', 'V7': '𓍨', 'V13': '𓍱', 'V16': '𓍴', 'V20': '𓍸', 'V22': '𓍺', 'V24': '𓍼', 'V28': '𓎀', 'V29': '𓎁', 'V30': '𓎂', 'V31': '𓎃',
        'W3': '𓎛', 'W9': '𓎡', 'W10': '𓎢', 'W11': '𓎣', 'W14': '𓎦', 'W15': '𓎧', 'W17': '𓎩', 'W18': '𓎪', 'W19': '𓎫', 'W22': '𓎮', 'W24': '𓎰', 'W25': '𓎱',
        'X1': '𓎛', 'X2': '𓎜', 'X4': '𓎟', 'X8': '𓎤',
        'Y1': '𓏏', 'Y2': '𓏐', 'Y3': '𓏑', 'Y5': '𓏞',
        'Z1': '𓏤', 'Z2': '𓏥', 'Z3': '𓏦', 'Z4': '𓏧', 'Z5': '𓏨', 'Z6': '𓏩', 'Z7': '𓏪', 'Z11': '𓏭',
        'Aa1': '𓐍', 'Aa2': '𓐎', 'Aa11': '𓐗', 'Aa13': '𓐙', 'Aa15': '𓐛', 'Aa17': '𓐝', 'Aa20': '𓐠', 'Aa27': '𓐧', 'Aa28': '𓐨',
        
        // Phonetic values (lowercase) - WikiHiero standard mappings
        'mA': '�',   // U1 (WikiHiero standard, not M3)
        'A': '�',    // G1 - Egyptian vulture
        'a': '𓄿',    // G1 - Egyptian vulture (aleph)
        'i': '𓇋',    // M17 - flowering reed
        'y': '𓇌',    // M18 - two flowering reeds
        'w': '�',    // G43 - quail chick
        'b': '�',    // D58 - foot
        'p': '𓊪',    // P1 - stool
        'f': '𓆑',    // I9 - horned viper
        'm': '𓅓',    // G17 - owl
        'n': '𓈖',    // N35 - ripple of water
        'r': '𓂋',    // D21 - mouth
        'h': '𓉔',    // O4 - reed shelter
        's': '�',    // S29 - folded cloth
        'S': '�',    // N37 - Sh sound
        'q': '𓈎',    // N29 - Q sound
        'k': '𓎡',    // W9 - K sound
        't': '�',    // X1 - bread loaf
        'd': '�',    // D46 - hand
        'D': '𓆓',    // I10 - Dj sound
        'nfr': '�', // F35 - common word
        'ra': '�',   // N5 - sun
        'kA': '𓂜',   // D28 - ka
    };
    
    // Split by separators and convert
    const parts = cleanCode.split(/[\s:\-&*]+/);
    let result = '';
    
    for (const part of parts) {
        if (!part || part.includes('_')) continue;
        
        // Try to map the code - gardinerCodepoints contains Unicode strings, not numbers
        const glyph = gardinerCodepoints[part] || gardinerCodepoints[part.toUpperCase()];
        if (glyph) {
            result += glyph;
        }
    }
    
    return result;
}

// Language code to name mapping
const languageNames = {
    'egy': 'Egyptian',
    'egy-lat': 'Late Egyptian',
    'dem': 'Demotic',
    'egx-dem': 'Demotic',
    'cop': 'Coptic',
    'cop-old': 'Old Coptic',
    'cop-sah': 'Sahidic Coptic',
    'cop-boh': 'Bohairic Coptic',
    'cop-akh': 'Akhmimic Coptic',
    'cop-lyc': 'Lycopolitan Coptic',
    'cop-fay': 'Fayyumic Coptic',
    'cop-her': 'Hermopolitan Coptic',
    'cop-oxy': 'Oxyrhynchite Coptic',
    'cop-kkk': 'Coptic (dialect)',
    'cop-ply': 'Proto-Coptic',
    'cop-ppp': 'Coptic (dialect)',
    'grc': 'Ancient Greek',
    'grc-koi': 'Koine Greek',
    'la': 'Latin',
    'ar': 'Arabic',
    'arz': 'Egyptian Arabic',
    'he': 'Hebrew',
    'hbo': 'Biblical Hebrew',
    'arc': 'Aramaic',
    'arc-imp': 'Imperial Aramaic',
    'akk': 'Akkadian',
    'akk-nas': 'Neo-Assyrian',
    'akk-nbb': 'Neo-Babylonian',
    'akk-mbb': 'Middle Babylonian',
    'xmr': 'Meroitic',
    'phn': 'Phoenician',
    'uga': 'Ugaritic',
    'syc': 'Classical Syriac',
    'gez': 'Geez',
    'xcl': 'Old Armenian',
    'peo': 'Old Persian',
    'elx-ach': 'Achaemenid Elamite',
    'sem-tha': 'Thamudic',
    'gmy': 'Mycenaean Greek',
    'ota': 'Ottoman Turkish',
    'en': 'English',
    'enm': 'Middle English',
    'fr': 'French',
    'fro': 'Old French',
    'xno': 'Anglo-Norman',
    'de': 'German',
    'it': 'Italian',
    'es': 'Spanish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'gl': 'Galician',
    'ru': 'Russian',
    'pl': 'Polish',
    'sv': 'Swedish',
    'el': 'Modern Greek',
    'tr': 'Turkish',
    'fa': 'Persian',
    'ps': 'Pashto',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'mt': 'Maltese',
    'onw': 'Old Nubian',
    'nyi': 'Ama',
    'fia': 'Nobiin',
    'myz': 'Classical Mandaic',
    'kzh': 'Dongolawi',
    'inm': 'Minaean'
};

// Get human-readable language name
function getLanguageName(code) {
    return languageNames[code] || code;
}

// Load parsed lemma data
async function loadParsedLemmas() {
    try {
        // Load Egyptian lemmas
        try {
            const egyResponse = await fetch('./egyptian_lemmas_parsed_mwp.json');
            if (egyResponse.ok) {
                egyptianLemmas = await egyResponse.json();
                console.log('Loaded Egyptian lemmas:', Object.keys(egyptianLemmas).length);
            }
        } catch (e) {
            console.warn('Could not load Egyptian lemmas:', e);
        }
        
        // Load Demotic lemmas
        try {
            const demResponse = await fetch('./demotic_lemmas_parsed_mwp.json');
            if (demResponse.ok) {
                demoticLemmas = await demResponse.json();
                console.log('Loaded Demotic lemmas:', Object.keys(demoticLemmas).length);
            }
        } catch (e) {
            console.warn('Could not load Demotic lemmas:', e);
        }
        
        // Load Coptic lemmas
        try {
            const copResponse = await fetch('./coptic_lemmas_parsed_mwp.json');
            if (copResponse.ok) {
                copticLemmas = await copResponse.json();
                console.log('Loaded Coptic lemmas:', Object.keys(copticLemmas).length);
            }
        } catch (e) {
            console.warn('Could not load Coptic lemmas:', e);
        }
    } catch (error) {
        console.warn('Error loading parsed lemmas:', error);
    }
}

// Get parsed data for a node
function getParsedDataForNode(node) {
    const form = node.form;
    
    if (node.language === 'egy' && egyptianLemmas[form]) {
        return egyptianLemmas[form];
    } else if (node.language === 'dem' && demoticLemmas[form]) {
        return demoticLemmas[form];
    } else if (node.language.startsWith('cop') && copticLemmas[form]) {
        return copticLemmas[form];
    }
    
    return null;
}

// Extract all hieroglyphic forms from parsed data
// If etymologyIndex is provided, only extract from that specific etymology
function getAllHieroglyphsFromParsed(parsedData, etymologyIndex = null) {
    const hieroglyphs = [];
    
    if (!parsedData || !parsedData.etymologies) return hieroglyphs;
    
    // Filter etymologies if index is specified
    const etymologiesToProcess = etymologyIndex !== null
        ? parsedData.etymologies.filter((etym, idx) => {
            // Match by etymology_number if available, otherwise by index
            if (etym.etymology_number !== undefined) {
                return etym.etymology_number === etymologyIndex + 1; // etymology_number is 1-indexed
            }
            return idx === etymologyIndex; // fallback to 0-indexed
          })
        : parsedData.etymologies;
    
    // Loop through filtered etymologies and definitions to find alternative forms
    etymologiesToProcess.forEach(etym => {
        if (etym.definitions) {
            etym.definitions.forEach(def => {
                // Check for alternative_forms array
                if (def.alternative_forms && Array.isArray(def.alternative_forms)) {
                    def.alternative_forms.forEach(alt => {
                        if (alt.hieroglyphs) {
                            hieroglyphs.push({
                                code: alt.hieroglyphs,
                                transliteration: alt.transliteration || ''
                            });
                        }
                    });
                }
                
                // Check the head parameter (main form)
                if (def.parameters && def.parameters.includes('head=<hiero>')) {
                    const match = def.parameters.match(/head=(<hiero>.*?<\/hiero>)/);
                    if (match) {
                        hieroglyphs.unshift({  // Add to beginning as it's the main form
                            code: match[1],
                            transliteration: '(main form)'
                        });
                    }
                }
            });
        }
    });
    
    return hieroglyphs;
}

// Build Wiktionary URL for a node
function getWiktionaryUrl(node, network) {
    // Map language codes to Wiktionary language sections
    const langMap = {
        'egy': 'Egyptian',
        'dem': 'Demotic',
        'egx-dem': 'Demotic',
        'cop': 'Coptic',
        'cop-boh': 'Coptic',
        'cop-sah': 'Coptic',
        'cop-old': 'Coptic',
        'cop-akh': 'Coptic',
        'cop-fay': 'Coptic',
        'cop-lyc': 'Coptic',
        'cop-her': 'Coptic',
        'cop-kkk': 'Coptic',
        'cop-oxy': 'Coptic',
        'cop-ply': 'Coptic',
        'cop-ppp': 'Coptic'
    };
    
    const wiktLang = langMap[node.language] || node.language;
    const form = encodeURIComponent(node.form);
    
    return `https://en.wiktionary.org/wiki/${form}#${wiktLang}`;
}

// Try to open Wiktionary page, fallback to parent if it doesn't exist
async function openWiktionaryPage(node, network) {
    const url = getWiktionaryUrl(node, network);
    
    // Try to check if the page exists by fetching it
    // Note: CORS will prevent this, so we just open in new tab
    // The browser will handle if page doesn't exist
    
    // Find parent node to use as fallback
    const parentEdge = network.edges.find(e => e.to === node.id);
    
    if (parentEdge) {
        const parentNode = network.nodes.find(n => n.id === parentEdge.from);
        if (parentNode) {
            const parentUrl = getWiktionaryUrl(parentNode, network);
            // Open both in new tabs - user can close the one that doesn't work
            // Or we show them a choice
            const message = `Opening Wiktionary page for "${node.form}".\nIf that page doesn't exist, try the parent: "${parentNode.form}"`;
            console.log(message);
        }
    }
    
    // Open the main URL
    window.open(url, '_blank');
}

// Load network data
async function loadNetworks() {
    try {
        // Load from current directory
        const response = await fetch('./lemma_networks.json');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        networks = await response.json();
        
        document.getElementById('totalNetworks').textContent = networks.length.toLocaleString();
        document.getElementById('graph').innerHTML = '<p class="loading">Network data loaded. Search for a lemma or click "Random Network" to begin.</p>';
        
        // Enable buttons
        document.getElementById('searchBtn').disabled = false;
        document.getElementById('randomBtn').disabled = false;
        
        // Check URL parameters for direct lemma access
        const urlParams = new URLSearchParams(window.location.search);
        const lemmaId = urlParams.get('lemma');
        if (lemmaId) {
            selectNetwork(lemmaId);
        }
        
    } catch (error) {
        document.getElementById('graph').innerHTML = `<p class="error">Error loading data: ${error.message}</p>`;
    }
}

// Search for networks
function searchNetworks(query) {
    if (!query || query.length < 2) return [];
    
    query = query.toLowerCase();
    const results = [];
    const seenNetworks = new Set(); // Track networks we've already added
    
    for (const network of networks) {
        // Skip if we've already added this network
        if (seenNetworks.has(network.network_id)) continue;
        
        // Search in all nodes
        for (const node of network.nodes) {
            const form = (node.form || '').toLowerCase();
            const meanings = (node.meanings || []).join(' ').toLowerCase();
            const lang = node.language || '';
            
            if (form.includes(query) || meanings.includes(query)) {
                results.push({
                    network: network,
                    node: node,
                    matchType: form.includes(query) ? 'form' : 'meaning'
                });
                seenNetworks.add(network.network_id);
                break; // Only add each network once
            }
        }
        if (results.length >= 50) break; // Limit to 50 networks
    }
    
    // Sort results: exact matches first, then by number of nodes (larger networks first)
    results.sort((a, b) => {
        const aExact = a.node.form.toLowerCase() === query;
        const bExact = b.node.form.toLowerCase() === query;
        if (aExact && !bExact) return -1;
        if (!aExact && bExact) return 1;
        return b.network.nodes.length - a.network.nodes.length;
    });
    
    return results;
}

// Display search suggestions
function showSuggestions(results) {
    const suggestionsDiv = document.getElementById('suggestions');
    
    if (results.length === 0) {
        suggestionsDiv.style.display = 'none';
        return;
    }
    
    suggestionsDiv.innerHTML = results.map(result => {
        const node = result.node;
        const network = result.network;
        const form = node.form;
        const meanings = node.meanings || [];
        const meaning = meanings.length > 0 
            ? meanings[0].substring(0, 80) + (meanings[0].length > 80 ? '...' : '')
            : 'No meaning available';
        
        return `
            <div class="suggestion-item" onclick="selectNetwork('${network.network_id}')">
                <strong>${form}</strong> (${node.language})
                <br><small>${meaning}</small>
                <br><small style="color: #999;">Network ID: ${network.network_id} • ${network.nodes.length} nodes</small>
            </div>
        `;
    }).join('');
    
    suggestionsDiv.style.display = 'block';
}

// Select and visualize a network
function selectNetwork(networkId) {
    const network = networks.find(n => n.network_id === networkId);
    if (!network) return;
    
    currentNetwork = network;
    document.getElementById('suggestions').style.display = 'none';
    
    // Update URL without reloading page
    const url = new URL(window.location);
    url.searchParams.set('lemma', networkId);
    window.history.pushState({}, '', url);
    
    visualizeNetwork(network);
}

// Get color based on language
function getNodeColor(language) {
    if (language === 'egy') return '#ff6b6b';
    if (language === 'dem') return '#4ecdc4';
    if (language.startsWith('cop')) return '#95e1d3';
    return '#ddd';
}

// Get edge color based on type
function getEdgeColor(type) {
    if (type === 'EVOLVES') return '#e74c3c';
    if (type === 'DESCENDS') return '#3498db';
    if (type === 'VARIANT') return '#95a5a6';
    if (type === 'DERIVED') return '#f39c12';      // Orange for derived terms
    if (type === 'COMPONENT') return '#9b59b6';    // Purple for components
    return '#999';
}

// Get edge style based on type
function getEdgeStyle(type) {
    if (type === 'VARIANT') return '5,5'; // Dashed
    if (type === 'COMPONENT') return '3,3'; // Dotted for components
    return '0'; // Solid
}

// Visualize network using D3.js force-directed graph
function visualizeNetwork(network) {
    // Update stats
    document.getElementById('currentNodes').textContent = network.nodes.length;
    document.getElementById('currentEdges').textContent = network.edges.length;
    
    const languages = new Set(network.nodes.map(n => n.language));
    document.getElementById('languages').textContent = languages.size;
    
    // Clear previous visualization
    const container = document.getElementById('graph');
    container.innerHTML = '';
    
    // Set up SVG
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Add zoom behavior
    const g = svg.append('g');
    
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Create node and link data
    const nodes = network.nodes.map(n => ({
        ...n,
        id: n.id,
        label: n.form || n.id,
        isRoot: false  // No root node concept in merged networks
    }));
    
    const links = network.edges.map(e => ({
        source: e.from,
        target: e.to,
        type: e.type,
        ...e
    }));
    
    // Create force simulation
    simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links)
            .id(d => d.id)
            .distance(d => {
                // Different distances for different edge types
                if (d.type === 'VARIANT') return 80;      // Keep variants close
                if (d.type === 'DERIVED') return 100;     // Derived terms fairly close
                if (d.type === 'COMPONENT') return 120;   // Components a bit further
                return 150;                                // EVOLVES and DESCENDS further apart
            }))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));
    
    // Create arrow markers for directed edges
    svg.append('defs').selectAll('marker')
        .data(['EVOLVES', 'DESCENDS', 'VARIANT', 'DERIVED', 'COMPONENT'])
        .enter().append('marker')
        .attr('id', d => `arrow-${d}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', d => getEdgeColor(d));
    
    // Create reverse arrow markers for VARIANT edges (double-sided)
    svg.select('defs').append('marker')
        .attr('id', 'arrow-VARIANT-reverse')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', -15)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M10,-5L0,0L10,5')
        .attr('fill', getEdgeColor('VARIANT'));
    
    // Create links
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .enter().append('line')
        .attr('stroke', d => getEdgeColor(d.type))
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', d => getEdgeStyle(d.type))
        .attr('marker-end', d => `url(#arrow-${d.type})`)
        .attr('marker-start', d => d.type === 'VARIANT' ? 'url(#arrow-VARIANT-reverse)' : null);
    
    // Add tooltips to links
    link.append('title')
        .text(d => {
            const typeDescriptions = {
                'EVOLVES': 'Temporal evolution within same language',
                'DESCENDS': 'Cross-language descent',
                'VARIANT': 'Dialectal or spelling variant',
                'DERIVED': 'Derivational morphology (affixation)',
                'COMPONENT': 'Component of compound word'
            };
            return typeDescriptions[d.type] || d.type;
        });
    
    // Create nodes
    const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter().append('g')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circles
    node.append('circle')
        .attr('r', d => d.isRoot ? 20 : 15)
        .attr('fill', d => getNodeColor(d.language))
        .attr('stroke', d => d.isRoot ? '#ffd700' : '#333')
        .attr('stroke-width', d => d.isRoot ? 4 : 2)
        .style('cursor', 'pointer')
        .on('mouseover', showNodeInfo)
        .on('mouseout', hideNodeInfo)
        .on('click', (event, d) => {
            event.stopPropagation();
            showLightbox(d, network);
        });
    
    // Add labels
    node.append('text')
        .text(d => d.label)
        .attr('x', 0)
        .attr('y', 30)
        .attr('text-anchor', 'middle')
        .attr('font-size', '12px')
        .attr('font-weight', d => d.isRoot ? 'bold' : 'normal')
        .attr('fill', '#333');
    
    // Add period/dialect labels
    node.append('text')
        .text(d => d.period || d.dialect || '')
        .attr('x', 0)
        .attr('y', 45)
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', '#666')
        .attr('font-style', 'italic');
    
    // Update positions on each tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // Zoom to fit all nodes after simulation stabilizes
    simulation.on('end', () => {
        // Calculate bounding box of all nodes
        const padding = 50;
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        nodes.forEach(d => {
            if (d.x < minX) minX = d.x;
            if (d.y < minY) minY = d.y;
            if (d.x > maxX) maxX = d.x;
            if (d.y > maxY) maxY = d.y;
        });
        
        // Calculate scale to fit all nodes in viewport
        const dx = maxX - minX;
        const dy = maxY - minY;
        const scale = Math.min(
            (width - padding * 2) / dx,
            (height - padding * 2) / dy,
            2  // Don't zoom in too much for small networks
        );
        
        // Calculate translate to center the network
        const translateX = width / 2 - scale * (minX + maxX) / 2;
        const translateY = height / 2 - scale * (minY + maxY) / 2;
        
        // Apply the transform
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

// Show node information on hover
function showNodeInfo(event, d) {
    // Clear any pending hide timeout
    if (hoverTimeout) {
        clearTimeout(hoverTimeout);
        hoverTimeout = null;
    }
    
    const infoDiv = document.getElementById('nodeInfo');
    const parsedData = getParsedDataForNode(d);
    
    let html = `
        <h3>${d.form}</h3>
        <p><strong>Language:</strong> ${getLanguageName(d.language)}</p>
    `;
    
    // Try to get hieroglyphs from parsed data or node data
    let hieroglyphForms = [];
    if (parsedData) {
        // Pass the node's etymology_index to get only relevant hieroglyphs
        const nodeEtymIndex = d.etymology_index !== undefined ? d.etymology_index : 0;
        hieroglyphForms = getAllHieroglyphsFromParsed(parsedData, nodeEtymIndex);
    }
    
    if (hieroglyphForms.length > 0) {
        // Show first (main) form in tooltip using WikiHiero images
        const mainForm = hieroglyphForms[0];
        const cleanCode = mainForm.code.replace(/<\/?hiero>/g, '').trim();
        const renderedGlyphs = renderHieroglyphs(mainForm.code);
        
        html += `<p><strong>Hieroglyphs:</strong> ${renderedGlyphs}</p>`;
        html += `<p style="font-size: 0.85em; color: #666;"><em>MdC:</em> ${cleanCode}</p>`;
    } else if (d.hieroglyphs) {
        const cleanCode = d.hieroglyphs.replace(/<\/?hiero>/g, '').trim();
        const renderedGlyphs = renderHieroglyphs(d.hieroglyphs);
        
        html += `<p><strong>Hieroglyphs:</strong> ${renderedGlyphs}</p>`;
        html += `<p style="font-size: 0.85em; color: #666;"><em>MdC:</em> ${cleanCode}</p>`;
    }
    
    if (d.part_of_speech && d.part_of_speech !== 'unknown') {
        html += `<p><strong>Part of Speech:</strong> ${d.part_of_speech}</p>`;
    }
    
    if (d.period) {
        html += `<p><strong>Period:</strong> ${d.period}</p>`;
    }
    
    if (d.dialect) {
        html += `<p><strong>Dialect:</strong> ${d.dialect}</p>`;
    }
    
    if (d.meanings && d.meanings.length > 0) {
        html += `<div class="meanings"><strong>Meanings:</strong><ul>`;
        d.meanings.slice(0, 3).forEach(m => {
            const cleaned = m.replace(/\{\{.*?\}\}/g, '').substring(0, 100);
            html += `<li>${cleaned}${m.length > 100 ? '...' : ''}</li>`;
        });
        html += `</ul></div>`;
    }
    
    html += `<p style="margin-top: 10px; color: #0066cc; font-size: 0.9em;">💡 Click node for full details</p>`;
    
    infoDiv.innerHTML = html;
    infoDiv.style.display = 'block';
    infoDiv.style.left = (event.pageX + 15) + 'px';
    infoDiv.style.top = (event.pageY + 15) + 'px';
}

// Hide node information with delay
function hideNodeInfo() {
    // Add a small delay before hiding to allow moving to the tooltip
    hoverTimeout = setTimeout(() => {
        const infoDiv = document.getElementById('nodeInfo');
        infoDiv.style.display = 'none';
    }, 300);
}

// Keep tooltip visible when hovering over it
function setupTooltipHover() {
    const infoDiv = document.getElementById('nodeInfo');
    
    infoDiv.addEventListener('mouseenter', () => {
        if (hoverTimeout) {
            clearTimeout(hoverTimeout);
            hoverTimeout = null;
        }
    });
    
    infoDiv.addEventListener('mouseleave', () => {
        hideNodeInfo();
    });
}

// Show lightbox with full node data
function showLightbox(node, network) {
    const lightbox = document.getElementById('lightbox');
    const content = document.getElementById('lightboxContent');
    
    const wiktUrl = getWiktionaryUrl(node, network);
    const parsedData = getParsedDataForNode(node);
    
    let html = `
        <h2>${node.form}</h2>
        
        <a href="${wiktUrl}" target="_blank" class="wiktionary-link">
            📖 View on Wiktionary
        </a>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Language</div>
                <div class="info-value">${getLanguageName(node.language)}</div>
            </div>
    `;
    
    if (node.transliteration && node.transliteration !== node.form) {
        html += `
            <div class="info-item">
                <div class="info-label">Transliteration</div>
                <div class="info-value">${node.transliteration}</div>
            </div>
        `;
    }
    
    if (node.period) {
        html += `
            <div class="info-item">
                <div class="info-label">Period</div>
                <div class="info-value">${node.period}</div>
            </div>
        `;
    }
    
    if (node.dialect) {
        html += `
            <div class="info-item">
                <div class="info-label">Dialect</div>
                <div class="info-value">${node.dialect}</div>
            </div>
        `;
    }
    
    html += `</div>`;
    
    // Display hieroglyphs if available
    let hieroglyphForms = [];
    if (parsedData) {
        // Pass the node's etymology_index to get only relevant hieroglyphs
        const nodeEtymIndex = node.etymology_index !== undefined ? node.etymology_index : 0;
        hieroglyphForms = getAllHieroglyphsFromParsed(parsedData, nodeEtymIndex);
    }
    
    if (hieroglyphForms.length > 0) {
        html += `
            <div class="lightbox-section">
                <h3>Hieroglyphic Writing</h3>
                <div style="display: flex; flex-direction: column; gap: 16px;">
        `;
        
        hieroglyphForms.forEach((form, idx) => {
            const cleanCode = form.code.replace(/<\/?hiero>/g, '').trim();
            const renderedGlyphs = renderHieroglyphs(form.code);
            const label = idx === 0 ? 'Main form' : form.transliteration || 'Alternative form';
            
            html += `
                <div style="border-left: 3px solid #8B4513; padding: 12px; background: #faf9f7; border-radius: 4px;">
                    <div style="font-size: 0.9em; color: #666; margin-bottom: 8px; font-weight: 500;">${label}</div>
                    <div style="margin: 8px 0;">${renderedGlyphs}</div>
                    <div style="font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9em; color: #999; margin-top: 6px;">MdC: ${cleanCode}</div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    } else if (node.hieroglyphs) {
        const cleanCode = node.hieroglyphs.replace(/<\/?hiero>/g, '').trim();
        const renderedGlyphs = renderHieroglyphs(node.hieroglyphs);
        
        html += `
            <div class="lightbox-section">
                <h3>Hieroglyphic Writing</h3>
                <div style="margin: 12px 0;">${renderedGlyphs}</div>
                <div style="font-family: 'Consolas', 'Monaco', monospace; font-size: 0.95em; color: #999;">MdC: ${cleanCode}</div>
            </div>
        `;
    }
    
    // Display parsed data if available
    if (parsedData) {
        // Pronunciations
        if (parsedData.pronunciations && parsedData.pronunciations.length > 0) {
            const nonEmpty = parsedData.pronunciations.filter(p => p && p.trim());
            if (nonEmpty.length > 0) {
                html += `
                    <div class="lightbox-section">
                        <h3>Pronunciations</h3>
                        <ul>
                `;
                nonEmpty.forEach(p => {
                    html += `<li>${p}</li>`;
                });
                html += `</ul></div>`;
            }
        }
        
        // Etymology - only show the etymology relevant to this specific node
        if (parsedData.etymologies && parsedData.etymologies.length > 0) {
            // Get the etymology index for this node (default to 0 if not set)
            const nodeEtymIndex = node.etymology_index !== undefined ? node.etymology_index : 0;
            
            // Only process the etymology that matches this node
            const relevantEtyms = parsedData.etymologies.filter((etym, idx) => {
                // Match by etymology_number if available, otherwise by index
                if (etym.etymology_number !== undefined) {
                    return etym.etymology_number === nodeEtymIndex + 1; // etymology_number is 1-indexed
                }
                return idx === nodeEtymIndex; // fallback to 0-indexed
            });
            
            relevantEtyms.forEach((etym, idx) => {
                html += `<div class="lightbox-section">`;
                
                // Only show etymology number if the original lemma has multiple etymologies
                if (parsedData.etymologies.length > 1) {
                    html += `<h3>Etymology ${etym.etymology_number || nodeEtymIndex + 1}</h3>`;
                } else {
                    html += `<h3>Etymology</h3>`;
                }
                
                if (etym.etymology_text) {
                    const cleanedText = etym.etymology_text
                        .replace(/===Etymology \d+===/g, '')
                        .replace(/\{\{[^}]+\}\}/g, (match) => {
                            // Simple template parser - extract readable text
                            const parts = match.slice(2, -2).split('|');
                            return parts[parts.length - 1] || '';
                        })
                        .trim();
                    
                    if (cleanedText) {
                        html += `<p>${cleanedText}</p>`;
                    }
                }
                
                // Definitions for this etymology
                if (etym.definitions && etym.definitions.length > 0) {
                    etym.definitions.forEach(def => {
                        if (def.part_of_speech) {
                            html += `<h4 style="margin-top: 15px; color: #1e3c72;">${def.part_of_speech}</h4>`;
                        }
                        
                        if (def.definitions && def.definitions.length > 0) {
                            html += `<ol style="margin-left: 20px;">`;
                            def.definitions.forEach(d => {
                                // Clean up templates and formatting
                                const cleaned = d
                                    .replace(/\{\{[^}]+\}\}/g, '')
                                    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2')
                                    .replace(/\[\[([^\]]+)\]\]/g, '$1')
                                    .trim();
                                
                                if (cleaned && !cleaned.startsWith('{{') && cleaned.length > 2) {
                                    html += `<li>${cleaned}</li>`;
                                }
                            });
                            html += `</ol>`;
                        }
                        
                        // Alternative forms
                        if (def.alternative_forms && def.alternative_forms.length > 0) {
                            html += `<p><strong>Alternative forms:</strong></p><ul>`;
                            def.alternative_forms.forEach(alt => {
                                let altText = '';
                                if (alt.transliteration) altText += alt.transliteration;
                                if (alt.hieroglyphs) altText += ` (${alt.hieroglyphs})`;
                                if (alt.date) altText += ` — ${alt.date}`;
                                if (altText) {
                                    html += `<li>${altText}</li>`;
                                }
                            });
                            html += `</ul>`;
                        }
                        
                        // Usage notes
                        if (def.usage_notes) {
                            const cleanedNotes = def.usage_notes
                                .replace(/\{\{[^}]+\}\}/g, '')
                                .trim();
                            if (cleanedNotes) {
                                html += `<p><strong>Usage notes:</strong> ${cleanedNotes}</p>`;
                            }
                        }
                        
                        // Derived terms
                        if (def.derived_terms && def.derived_terms.length > 0) {
                            html += `<p><strong>Derived terms:</strong> ${def.derived_terms.join(', ')}</p>`;
                        }
                        
                        // Descendants
                        if (def.descendants && def.descendants.length > 0) {
                            html += `<p><strong>Descendants:</strong></p><ul>`;
                            def.descendants.forEach(desc => {
                                const langName = getLanguageName(desc.language);
                                html += `<li>${desc.word} (${langName})</li>`;
                            });
                            html += `</ul>`;
                        }
                    });
                }
                
                html += `</div>`;
            });
        }
    } else {
        // Fallback to node.meanings if no parsed data
        if (node.meanings && node.meanings.length > 0) {
            html += `
                <div class="lightbox-section">
                    <h3>Meanings</h3>
                    <ul>
            `;
            node.meanings.forEach(m => {
                html += `<li>${m}</li>`;
            });
            html += `
                    </ul>
                </div>
            `;
        }
    }
    
    // Find related nodes (parents and children)
    const parents = network.edges.filter(e => e.to === node.id);
    const children = network.edges.filter(e => e.from === node.id);
    
    if (parents.length > 0 || children.length > 0) {
        html += `<div class="lightbox-section"><h3>Relationships in Network</h3>`;
        
        if (parents.length > 0) {
            html += `<p><strong>Derived from:</strong></p><ul>`;
            parents.forEach(edge => {
                const parentNode = network.nodes.find(n => n.id === edge.from);
                if (parentNode) {
                    const langName = getLanguageName(parentNode.language);
                    html += `<li>${parentNode.form} (${langName}) — ${edge.type}</li>`;
                }
            });
            html += `</ul>`;
        }
        
        if (children.length > 0) {
            html += `<p><strong>Descendants:</strong></p><ul>`;
            children.forEach(edge => {
                const childNode = network.nodes.find(n => n.id === edge.to);
                if (childNode) {
                    const langName = getLanguageName(childNode.language);
                    html += `<li>${childNode.form} (${langName}) — ${edge.type}</li>`;
                }
            });
            html += `</ul>`;
        }
        
        html += `</div>`;
    }
    
    content.innerHTML = html;
    lightbox.style.display = 'flex';
}

// Close lightbox
function closeLightbox() {
    document.getElementById('lightbox').style.display = 'none';
}

// Show random network
function showRandomNetwork() {
    if (networks.length === 0) return;
    
    const randomIndex = Math.floor(Math.random() * networks.length);
    const network = networks[randomIndex];
    selectNetwork(network.network_id);
}

// Event listeners
document.getElementById('searchInput').addEventListener('input', (e) => {
    const query = e.target.value;
    if (query.length >= 2) {
        const results = searchNetworks(query);
        showSuggestions(results);
    } else {
        document.getElementById('suggestions').style.display = 'none';
    }
});

document.getElementById('searchInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const query = e.target.value;
        const results = searchNetworks(query);
        if (results.length > 0) {
            selectNetwork(results[0].network.network_id);
        }
    }
});

document.getElementById('searchBtn').addEventListener('click', () => {
    const query = document.getElementById('searchInput').value;
    const results = searchNetworks(query);
    if (results.length > 0) {
        selectNetwork(results[0].network.network_id);
    }
});

document.getElementById('randomBtn').addEventListener('click', showRandomNetwork);

// Close suggestions when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('#searchInput') && !e.target.closest('#suggestions')) {
        document.getElementById('suggestions').style.display = 'none';
    }
});

// Close lightbox when clicking on overlay
document.getElementById('lightbox').addEventListener('click', (e) => {
    if (e.target.id === 'lightbox') {
        closeLightbox();
    }
});

// Close lightbox with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeLightbox();
    }
});

// Initialize
setupTooltipHover();
loadParsedLemmas();
loadNetworks();
