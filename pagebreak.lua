--- Return a block element causing a page break in the given format.
local function newpage(format)
  if format == 'docx' then
    local pagebreak = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    return pandoc.RawBlock('openxml', pagebreak)
  elseif format:match 'latex' then
    return pandoc.RawBlock('tex', '\\clearpage')
  else
    -- fall back to insert a form feed character
    return pandoc.Para{pandoc.Str '\f'}
  end
end

-- Filter function called on each RawBlock element.
function RawBlock (el)
  if el.text:find '\\newpage' then
    
    return newpage(FORMAT)
  end
  -- otherwise, leave the block unchanged
  return nil
end

function Str (el)
  if el.text:match 'Bref' then
    return "PROUT"
  end
end

function Link(el)
    if FORMAT:match 'latex' then
        el.content = pandoc.Strong(el)
        return el

    end
end
