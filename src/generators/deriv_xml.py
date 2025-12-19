"""Generate Deriv DBot (Blockly XML) from canonical IR.

Supported subset:
- Market: synthetic index R_50 by default.
- Contract: Rise/Fall (CALL purchase) with fixed stake/duration.
- Indicators: SMA, EMA, RSI (mapped to generic TA blocks: ta_sma, ta_ema, ta_rsi).
- Entry condition: first entry_long condition only; supports crossover/crossunder and simple comparisons.
- Exit condition: ignored (DBot lacks standard stop/close; would need custom risk logic).

This is a starter bridge; block type names may need adjustment to match the exact
Deriv account Blockly catalog. Export a sample bot from app.deriv.com/bot to
confirm block types/field enums, then extend mapping as needed.
"""

from typing import Dict, Any, List
import xml.etree.ElementTree as ET


def generate(ir: Dict[str, Any]) -> str:
    meta = ir.get("meta", {})
    indicators = ir.get("indicators", [])
    conditions = ir.get("conditions", {})

    # Build variable list from indicator ids
    var_names = [ind.get("id", f"ind{i}") for i, ind in enumerate(indicators)]

    # DBot XML root (matching ORSTAC samples)
    root = ET.Element(
        "xml",
        attrib={
            "xmlns": "http://www.w3.org/1999/xhtml",
            "is_dbot": "true",
            "collection": "false",
        },
    )

    # <variables>
    vars_el = ET.SubElement(root, "variables")
    for name in var_names:
        var = ET.SubElement(vars_el, "variable", attrib={"id": name})
        var.text = name

    # Root trade_definition block
    trade_def = _block(root, "trade_definition", block_id="trade_def", x="0", y="0")

    # Market / symbol (hard-coded to synthetic random R_100 for now)
    stmt_opts = ET.SubElement(trade_def, "statement", name="TRADE_OPTIONS")
    market_block = _block(stmt_opts, "trade_definition_market")
    _field(market_block, "MARKET_LIST", "synthetic_index")
    _field(market_block, "SUBMARKET_LIST", "random_index")
    _field(market_block, "SYMBOL_LIST", "R_100")

    tradetype_block = _block(market_block, "trade_definition_tradetype", use_next=True)
    _field(tradetype_block, "TRADETYPECAT_LIST", "callput")
    _field(tradetype_block, "TRADETYPE_LIST", "callput")

    contract_block = _block(tradetype_block, "trade_definition_contracttype", use_next=True)
    _field(contract_block, "TYPE_LIST", "both")

    candle_block = _block(contract_block, "trade_definition_candleinterval", use_next=True)
    _field(candle_block, "CANDLEINTERVAL_LIST", "60")

    restart_block = _block(candle_block, "trade_definition_restartonerror", use_next=True)
    _field(restart_block, "RESTARTONERROR", "TRUE")

    # Trade options (stake/payout/duration). Use stake with USD by default.
    # DBot usually nests amount/duration inside TRADE_OPTIONS via next chain.
    trademark_block = _block(restart_block, "trade_definition_trademark", use_next=True)
    _field(trademark_block, "TRADETYPECAT", "stake")
    _field(trademark_block, "AMOUNT", "1")
    _field(trademark_block, "CURRENCY", "USD")

    dur_block = _block(trademark_block, "trade_definition_duration", use_next=True)
    _field(dur_block, "DURATION", "5")
    _field(dur_block, "DURATIONTYPE", "m")

    # BEFOREPURCHASE stack (as separate block, matching ORSTAC style)
    before_block = _block(root, "before_purchase", block_id="before_purchase", x="0", y="160")
    stmt_before = ET.SubElement(before_block, "statement", name="BEFOREPURCHASE_STACK")
    chain = _build_indicator_chain_orstac(stmt_before, indicators)

    # Append entry condition with purchase
    _append_entry_condition_orstac(chain, conditions)

    # Serialize with pretty spacing
    _indent(root)
    return ET.tostring(root, encoding="unicode")


# Helpers -------------------------------------------------------------------

def _block(parent: ET.Element, block_type: str, block_id: str | None = None, x: str | None = None, y: str | None = None, use_next: bool = False) -> ET.Element:
    """Create a Blockly block element."""
    tag_parent = parent
    if use_next:
        tag_parent = ET.SubElement(parent, "next")
    attrib: Dict[str, str] = {"type": block_type}
    if block_id:
        attrib["id"] = block_id
    if x is not None:
        attrib["x"] = x
    if y is not None:
        attrib["y"] = y
    return ET.SubElement(tag_parent, "block", attrib=attrib)


def _field(block: ET.Element, name: str, value: str) -> ET.Element:
    field = ET.SubElement(block, "field", name=name)
    field.text = value
    return field


def _value(block: ET.Element, name: str) -> ET.Element:
    return ET.SubElement(block, "value", name=name)


def _statement(block: ET.Element, name: str) -> ET.Element:
    return ET.SubElement(block, "statement", name=name)


def _variables_set(parent: ET.Element, var_name: str, value_block: ET.Element) -> ET.Element:
    set_block = _block(parent, "variables_set")
    _field(set_block, "VAR", var_name)
    val = _value(set_block, "VALUE")
    val.append(value_block)
    return set_block


def _ohlc_block(field_name: str = "close") -> ET.Element:
    b = ET.Element("block", attrib={"type": "ohlc_values"})
    _field(b, "OHLCFIELD_LIST", field_name)
    _field(b, "CANDLEINTERVAL_LIST", "default")
    return b


def _indicator_block_orstac(ind: Dict[str, Any]) -> ET.Element:
    """Map indicator to ORSTAC-style statement block (sma_statement/ema_statement/rsi_statement)."""
    ind_type = ind.get("type", "SMA").upper()
    params = ind.get("params", {})
    period = str(params.get("period") or params.get("timeperiod") or params.get("length") or 14)

    block_type = None
    if ind_type == "SMA":
        block_type = "sma_statement"
    elif ind_type == "EMA":
        block_type = "ema_statement"
    elif ind_type == "RSI":
        block_type = "rsi_statement"
    else:
        block_type = "sma_statement"  # fallback

    b = ET.Element("block", attrib={"type": block_type})
    _field(b, "VARIABLE", ind.get("id", "ind"))

    stmt = _statement(b, "STATEMENT")
    # input_list
    inp_list = _block(stmt, "input_list")
    val_inp = _value(inp_list, "INPUT_LIST")
    val_inp.append(_ohlc_block("close"))
    # period
    period_block = _block(inp_list, "period", use_next=True)
    val_period = _value(period_block, "PERIOD")
    num = ET.Element("block", attrib={"type": "math_number"})
    _field(num, "NUM", period)
    val_period.append(num)

    return b


def _build_indicator_chain_orstac(parent: ET.Element, indicators: List[Dict[str, Any]]) -> ET.Element:
    """Build indicator *_statement blocks chained via next; return tail block for chaining."""
    if not indicators:
        return _block(parent, "controls_if")

    head = None
    prev = None
    for ind in indicators:
        stmt_block = _indicator_block_orstac(ind)
        if head is None:
            parent.append(stmt_block)
            head = stmt_block
        else:
            # chain via <next>
            n = ET.SubElement(prev, "next")
            n.append(stmt_block)
        prev = stmt_block
    return prev or parent


def _append_entry_condition_orstac(chain_tail: ET.Element, conditions: Dict[str, Any]) -> None:
    entry_conds = conditions.get("entry_long", []) if conditions else []
    if not entry_conds:
        return

    cond = entry_conds[0]
    expr = cond.get("expr_translated") or cond.get("expr") or ""
    if not expr:
        return

    if_block = _block(chain_tail, "controls_if", use_next=True)
    test_val = _value(if_block, "IF0")
    test_val.append(_expr_to_block_orstac(expr))
    do_stmt = _statement(if_block, "DO0")
    purchase = _block(do_stmt, "purchase")
    _field(purchase, "PURCHASE_LIST", "CALL")


def _expr_to_block_orstac(expr: str) -> ET.Element:
    """Expression mapper to ORSTAC-compatible blocks.

    Supports:
    - crossover(a, b) / ta.crossover(a, b) → logic_compare with prev values? (fallback to A>B)
    - crossunder(a, b) / ta.crossunder(a, b)
    - simple comparisons: >, <, >=, <=, ==, != mapped to OP codes GT, LT, GTE, LTE, EQ, NEQ.
    """
    e = expr.replace("ta.", "")
    e = e.replace("ind:", "")

    # comparisons first
    op_map = {
        ">=": "GTE",
        "<=": "LTE",
        ">": "GT",
        "<": "LT",
        "==": "EQ",
        "!": "NEQ",  # will handle != below
    }

    if "!=" in e:
        lhs, rhs = [s.strip() for s in e.split("!=", 1)]
        block = ET.Element("block", attrib={"type": "logic_compare"})
        _field(block, "OP", "NEQ")
        _value(block, "A").append(_var_or_number(lhs))
        _value(block, "B").append(_var_or_number(rhs))
        return block

    for sym, op_code in [(">=", "GTE"), ("<=", "LTE"), (">", "GT"), ("<", "LT"), ("==", "EQ")]:
        if sym in e:
            lhs, rhs = [s.strip() for s in e.split(sym, 1)]
            block = ET.Element("block", attrib={"type": "logic_compare"})
            _field(block, "OP", op_code)
            _value(block, "A").append(_var_or_number(lhs))
            _value(block, "B").append(_var_or_number(rhs))
            return block

    if "crossover" in e:
        a, b = _args2(e)
        # fallback: a > b
        block = ET.Element("block", attrib={"type": "logic_compare"})
        _field(block, "OP", "GT")
        _value(block, "A").append(_var_or_number(a))
        _value(block, "B").append(_var_or_number(b))
        return block
    if "crossunder" in e:
        a, b = _args2(e)
        block = ET.Element("block", attrib={"type": "logic_compare"})
        _field(block, "OP", "LT")
        _value(block, "A").append(_var_or_number(a))
        _value(block, "B").append(_var_or_number(b))
        return block

    block = ET.Element("block", attrib={"type": "logic_boolean"})
    _field(block, "BOOL", "FALSE")
    return block


def _args2(expr: str) -> List[str]:
    inside = expr[expr.find("(") + 1 : expr.rfind(")")]
    parts = [p.strip() for p in inside.split(",")]
    return parts if len(parts) == 2 else ["a", "b"]


def _var_get(name: str) -> ET.Element:
    b = ET.Element("block", attrib={"type": "variables_get"})
    _field(b, "VAR", name)
    return b


def _var_or_number(tok: str) -> ET.Element:
    try:
        float(tok)
        num = ET.Element("block", attrib={"type": "math_number"})
        _field(num, "NUM", tok)
        return num
    except Exception:
        return _var_get(tok)


def _indent(elem: ET.Element, level: int = 0) -> None:
    """Pretty-print indentation for ElementTree output."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
