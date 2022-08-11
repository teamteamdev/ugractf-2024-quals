using System.Runtime.CompilerServices;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using pastapp.Models;


namespace pastapp.Controllers;

public class LocalizationController : Controller
{
    ApplicationContext db;
    private readonly ILogger<LocalizationController> _logger;

    public LocalizationController(ILogger<LocalizationController> logger, ApplicationContext context)
    {
        _logger = logger;
        db = context;
    }

    public async Task<IActionResult> GetPageByLanguage()
    {
        var lang_id = HttpContext.Request.Headers.AcceptLanguage;
        var query = "SELECT * FROM \"Localizations\" WHERE \"LocaleCode\" = '" + lang_id + "'";
        try{
            var result = await db.Localizations.FromSql(FormattableStringFactory.Create(query)).ToListAsync();
            if (result.IsNullOrEmpty()) {
                return Content("Запрашиваемая локализация не найдена.");
            }
            var content = result[0].Content;
            return Content(content) ;
        }
        catch (Exception e){
            var message = "Произошла ошибка при загрузке локализации.";
            // uncomment to allow sql messages
            // message += e.Message;
            return Content(message);
        }
        
    }
}