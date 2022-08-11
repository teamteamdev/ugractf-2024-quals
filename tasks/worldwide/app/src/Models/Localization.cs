namespace pastapp.Models;
using System.ComponentModel.DataAnnotations;

public class Localization
{
    [Key]
    public string LocaleCode { get; set; }
    public string Content { get; set; }
}